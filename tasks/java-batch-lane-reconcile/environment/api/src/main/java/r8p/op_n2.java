package r8p;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.transaction.Transactional;
import java.util.List;
import org.springframework.stereotype.Component;
import r8p.dto.BatchRequest;
import r8p.dto.IngestResult;
import r8p.dto.LinePayload;
import r8p.dto.SnapshotView;
import r8p.entity.HeaderSlice;
import r8p.entity.LineSlice;
import r8p.entity.PartitionDim;
import r8p.event.LaneCommittedEvent;
import r8p.repo.HeaderRepo;
import r8p.repo.LineRepo;
import r8p.repo.PartitionRepo;
import org.springframework.context.ApplicationEventPublisher;

@Component
public class op_n2 {
  @PersistenceContext
  private EntityManager em;
  private final HeaderRepo headers;
  private final LineRepo lines;
  private final PartitionRepo partitions;
  private final ApplicationEventPublisher events;
  private final org.springframework.core.env.Environment env;

  public op_n2(
      HeaderRepo headers,
      LineRepo lines,
      PartitionRepo partitions,
      ApplicationEventPublisher events,
      org.springframework.core.env.Environment env) {
    this.headers = headers;
    this.lines = lines;
    this.partitions = partitions;
    this.events = events;
    this.env = env;
  }

  @Transactional
  public IngestResult op_n2(String label, BatchRequest chunk) {
    PartitionDim part =
        partitions.findById(label).orElseThrow(() -> new IllegalArgumentException("unknown label"));
    if (part.getActiveSlots() >= part.getCapSlots()) {
      recordAttempt(label, chunk, 0);
      return new IngestResult(0, part.getActiveSlots(), part.getRollupQty());
    }
    for (LinePayload row : chunk.getLines()) {
      if (row.getQty() <= 0 || env.getProperty("lane.fail-sku", "").equals(row.getSku())) {
        throw new IllegalArgumentException("abort");
      }
    }
    HeaderSlice hdr =
        headers
            .findByPartitionLabelAndExternalBizId(label, chunk.getExternalBizId())
            .orElseGet(
                () -> {
                  HeaderSlice h = new HeaderSlice();
                  h.setPartitionLabel(label);
                  h.setExternalBizId(chunk.getExternalBizId());
                  return headers.save(h);
                });
    em.flush();
    int accepted = 0;
    for (LinePayload row : chunk.getLines()) {
      LineSlice ln = new LineSlice();
      ln.setHeader(hdr);
      ln.setSku(row.getSku());
      ln.setQty(row.getQty());
      lines.save(ln);
      accepted++;
    }
    part.setActiveSlots(part.getActiveSlots() + accepted);
    partitions.save(part);
    em.flush();
    recordAttempt(label, chunk, accepted);
    events.publishEvent(new LaneCommittedEvent(label, chunk.getExternalBizId(), accepted));
    return new IngestResult(accepted, part.getActiveSlots(), part.getRollupQty());
  }

  public SnapshotView snapshot(String label) {
    long cnt =
        lines.countByHeaderPartitionLabel(label);
    PartitionDim part = partitions.findById(label).orElseThrow();
    return new SnapshotView(label, cnt, part.getRollupQty(), part.getActiveSlots());
  }

  @Transactional
  public void resetAll() {
    em.createNativeQuery("TRUNCATE lane_attempt, line_slice, header_slice RESTART IDENTITY CASCADE")
        .executeUpdate();
    em.createNativeQuery("UPDATE partition_dim SET active_slots=0, rollup_qty=0").executeUpdate();
  }

  private void recordAttempt(String label, BatchRequest chunk, int accepted) {
    em.createNativeQuery(
            "INSERT INTO lane_attempt(partition_label, external_biz_id, accepted_lines, payload) "
                + "VALUES (?1, ?2, ?3, cast(?4 as jsonb))")
        .setParameter(1, label)
        .setParameter(2, chunk.getExternalBizId())
        .setParameter(3, accepted)
        .setParameter(4, toJson(chunk))
        .executeUpdate();
  }

  private String toJson(BatchRequest chunk) {
    try {
      return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(chunk);
    } catch (Exception ex) {
      return "{}";
    }
  }
}
