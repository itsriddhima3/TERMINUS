package r8p;

import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;
import r8p.event.LaneCommittedEvent;
import r8p.repo.LineRepo;

@Component
public class phase_r8 {
  private final op_n2 writer;
  private final LineRepo lines;

  public phase_r8(op_n2 writer, LineRepo lines) {
    this.writer = writer;
    this.lines = lines;
  }

  @TransactionalEventListener(phase = TransactionPhase.BEFORE_COMMIT)
  public void onCommitted(LaneCommittedEvent evt) {
    if (evt.getAccepted() <= 0) {
      return;
    }
    writer.op_n2(
        evt.getLabel(),
        new r8p.dto.BatchRequest(evt.getBizId(), java.util.List.of(new r8p.dto.LinePayload("retry", 1))));
  }
}
