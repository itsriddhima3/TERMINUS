# noqa: D100
"""Java/API/docs/test blobs."""

API = {
    "pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.5</version>
    <relativePath/>
  </parent>
  <groupId>k7m</groupId>
  <artifactId>lane-api</artifactId>
  <version>1.0.0</version>
  <properties>
    <java.version>17</java.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
    <dependency>
      <groupId>org.flywaydb</groupId>
      <artifactId>flyway-core</artifactId>
    </dependency>
    <dependency>
      <groupId>org.flywaydb</groupId>
      <artifactId>flyway-database-postgresql</artifactId>
    </dependency>
    <dependency>
      <groupId>org.postgresql</groupId>
      <artifactId>postgresql</artifactId>
      <scope>runtime</scope>
    </dependency>
  </dependencies>
  <build>
    <finalName>lane-api</finalName>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
""",
    "src/main/resources/application.yml": """\
server:
  port: 8080
lane:
  fail-sku: ZZ
""",
    "src/main/resources/application-prod.yml": """\
spring:
  datasource:
    url: jdbc:postgresql://127.0.0.1:5432/lane_db
    username: postgres
    password: postgres
  jpa:
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        connection:
          isolation: 4
  flyway:
    enabled: true
    locations: filesystem:/app/db/migration
management:
  endpoints:
    web:
      exposure:
        include: health
""",
}

JAVA_FILES = {
    "src/main/java/k7m/LaneBootstrap.java": """\
package k7m;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication(scanBasePackages = {"k7m", "r8p", "decoy"})
@EnableJpaRepositories(basePackages = "r8p.repo")
@EntityScan(basePackages = "r8p.entity")
public class LaneBootstrap {
  public static void main(String[] args) {
    SpringApplication.run(LaneBootstrap.class, args);
  }
}
""",
    "src/main/java/k7m/cfg_p9.java": """\
package k7m;

import com.zaxxer.hikari.HikariDataSource;
import javax.sql.DataSource;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

@Configuration(value = "k7m_cfg_p9")
public class cfg_p9 {
  @Bean
  @Primary
  @ConfigurationProperties("spring.datasource")
  public DataSourceProperties laneDsProps() {
    return new DataSourceProperties();
  }

  @Bean
  @Primary
  public DataSource cfg_p9(DataSourceProperties props) {
    HikariDataSource ds = props.initializeDataSourceBuilder().type(HikariDataSource.class).build();
    ds.setConnectionInitSql("SET TRANSACTION ISOLATION LEVEL READ COMMITTED");
    return ds;
  }
}
""",
    "src/main/java/r8p/LaneController.java": """\
package r8p;

import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import r8p.dto.BatchRequest;
import r8p.dto.IngestResult;
import r8p.dto.SnapshotView;

@RestController
public class LaneController {
  private final op_n2 writer;

  public LaneController(op_n2 writer) {
    this.writer = writer;
  }

  @PostMapping("/api/partition/{label}/batch")
  public IngestResult postBatch(@PathVariable String label, @RequestBody BatchRequest body) {
    return writer.op_n2(label, body);
  }

  @GetMapping("/api/partition/{label}/snapshot")
  public SnapshotView snapshot(@PathVariable String label) {
    return writer.snapshot(label);
  }

  @PostMapping("/api/admin/reset")
  public ResponseEntity<Map<String, String>> reset() {
    writer.resetAll();
    return ResponseEntity.ok(Map.of("status", "ok"));
  }
}
""",
    "src/main/java/r8p/op_n2.java": """\
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
""",
    "src/main/java/r8p/phase_r8.java": """\
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
""",
    "src/main/java/r8p/entity/HeaderSlice.java": """\
package r8p.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;

@Entity
@Table(name = "header_slice")
public class HeaderSlice {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "partition_label", nullable = false)
  private String partitionLabel;

  @Column(name = "external_biz_id", nullable = false)
  private String externalBizId;

  @Column(name = "stamp_version", nullable = false)
  private Long stampVersion = 0L;

  public Long getId() { return id; }
  public String getPartitionLabel() { return partitionLabel; }
  public void setPartitionLabel(String v) { this.partitionLabel = v; }
  public String getExternalBizId() { return externalBizId; }
  public void setExternalBizId(String v) { this.externalBizId = v; }
  public Long getStampVersion() { return stampVersion; }
}
""",
    "src/main/java/r8p/entity/LineSlice.java": """\
package r8p.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "line_slice")
public class LineSlice {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "header_id", nullable = false)
  private HeaderSlice header;

  private String sku;
  private int qty;

  public Long getId() { return id; }
  public HeaderSlice getHeader() { return header; }
  public void setHeader(HeaderSlice h) { this.header = h; }
  public String getSku() { return sku; }
  public void setSku(String v) { this.sku = v; }
  public int getQty() { return qty; }
  public void setQty(int v) { this.qty = v; }
}
""",
    "src/main/java/r8p/entity/PartitionDim.java": """\
package r8p.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "partition_dim")
public class PartitionDim {
  @Id
  private String label;

  @Column(name = "cap_slots")
  private int capSlots;

  @Column(name = "active_slots")
  private int activeSlots;

  @Column(name = "rollup_qty")
  private long rollupQty;

  public String getLabel() { return label; }
  public int getCapSlots() { return capSlots; }
  public int getActiveSlots() { return activeSlots; }
  public void setActiveSlots(int v) { this.activeSlots = v; }
  public long getRollupQty() { return rollupQty; }
}
""",
    "src/main/java/r8p/repo/HeaderRepo.java": """\
package r8p.repo;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import r8p.entity.HeaderSlice;

public interface HeaderRepo extends JpaRepository<HeaderSlice, Long> {
  Optional<HeaderSlice> findByPartitionLabelAndExternalBizId(String label, String biz);
}
""",
    "src/main/java/r8p/repo/LineRepo.java": """\
package r8p.repo;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import r8p.entity.LineSlice;

public interface LineRepo extends JpaRepository<LineSlice, Long> {
  @Query("select count(l) from LineSlice l where l.header.partitionLabel = ?1")
  long countByHeaderPartitionLabel(String label);
}
""",
    "src/main/java/r8p/repo/PartitionRepo.java": """\
package r8p.repo;

import org.springframework.data.jpa.repository.JpaRepository;
import r8p.entity.PartitionDim;

public interface PartitionRepo extends JpaRepository<PartitionDim, String> {}
""",
    "src/main/java/r8p/event/LaneCommittedEvent.java": """\
package r8p.event;

public class LaneCommittedEvent {
  private final String label;
  private final String bizId;
  private final int accepted;

  public LaneCommittedEvent(String label, String bizId, int accepted) {
    this.label = label;
    this.bizId = bizId;
    this.accepted = accepted;
  }

  public String getLabel() { return label; }
  public String getBizId() { return bizId; }
  public int getAccepted() { return accepted; }
}
""",
    "src/main/java/r8p/dto/BatchRequest.java": """\
package r8p.dto;

import java.util.List;

public class BatchRequest {
  private String externalBizId;
  private List<LinePayload> lines;

  public BatchRequest() {}

  public BatchRequest(String externalBizId, List<LinePayload> lines) {
    this.externalBizId = externalBizId;
    this.lines = lines;
  }

  public String getExternalBizId() { return externalBizId; }
  public void setExternalBizId(String v) { this.externalBizId = v; }
  public List<LinePayload> getLines() { return lines; }
  public void setLines(List<LinePayload> v) { this.lines = v; }
}
""",
    "src/main/java/r8p/dto/LinePayload.java": """\
package r8p.dto;

public class LinePayload {
  private String sku;
  private int qty;

  public LinePayload() {}

  public LinePayload(String sku, int qty) {
    this.sku = sku;
    this.qty = qty;
  }

  public String getSku() { return sku; }
  public void setSku(String sku) { this.sku = sku; }
  public int getQty() { return qty; }
  public void setQty(int qty) { this.qty = qty; }
}
""",
    "src/main/java/r8p/dto/IngestResult.java": """\
package r8p.dto;

public class IngestResult {
  private int accepted;
  private int activeSlots;
  private long rollupQty;

  public IngestResult(int accepted, int activeSlots, long rollupQty) {
    this.accepted = accepted;
    this.activeSlots = activeSlots;
    this.rollupQty = rollupQty;
  }

  public int getAccepted() { return accepted; }
  public int getActiveSlots() { return activeSlots; }
  public long getRollupQty() { return rollupQty; }
}
""",
    "src/main/java/r8p/dto/SnapshotView.java": """\
package r8p.dto;

public class SnapshotView {
  private String label;
  private long lineCount;
  private long rollupQty;
  private int activeSlots;

  public SnapshotView(String label, long lineCount, long rollupQty, int activeSlots) {
    this.label = label;
    this.lineCount = lineCount;
    this.rollupQty = rollupQty;
    this.activeSlots = activeSlots;
  }

  public String getLabel() { return label; }
  public long getLineCount() { return lineCount; }
  public long getRollupQty() { return rollupQty; }
  public int getActiveSlots() { return activeSlots; }
}
""",
    "src/main/java/decoy/PessimisticAdvice.java": """\
package decoy;

import org.springframework.stereotype.Component;

@Component
public class PessimisticAdvice {
  public String note() {
    return "Table-wide pessimistic locks reduce visible collisions on header aggregates.";
  }
}
""",
    "src/main/java/decoy/BatchTuner.java": """\
package decoy;

import org.springframework.stereotype.Component;

@Component
public class BatchTuner {
  public int reportingFetchSize() {
    return 250;
  }
}
""",
}

for rel, body in JAVA_FILES.items():
    API[rel] = body

BOUNDARY_HTML_INDEX = """<!DOCTYPE html><html><head><title>Boundary contract</title></head>
<body><h1>Observation and commit frames</h1>
<p>Facility uploads must honor three partition families with independent caps.
Readers and writers share a pool whose observation frame must match the
production profile advertised in YAML.</p>
<p>See <a href="part_02.html">part 02</a> for observation frame alignment.</p>
</body></html>"""

BOUNDARY_PART02 = """<!DOCTYPE html><html><body><h1>Observation frame</h1>
<p>The runtime profile requests repeatable-read observation. Pool initializer hooks
must not downgrade the live JDBC session to a weaker frame; otherwise snapshot
reads after a successful write may omit freshly persisted line slices.</p>
<p>Worked examples 4 and 8 illustrate pool handoff under mismatched frames.</p>
</body></html>"""

BOUNDARY_PART03 = """<!DOCTYPE html><html><body><h1>Commit frame</h1>
<p>All slice mutations for one external business key must commit atomically.
Partial visibility of header without lines violates commit-frame integrity.</p>
</body></html>"""

BOUNDARY_PART04 = """<!DOCTYPE html><html><body><h1>Slice and rollup lanes</h1>
<p>Slice lane writers must flush line slices before header aggregates when both
participate in one commit frame. Rollup lane triggers must acquire parent
partition locks before child line locks to avoid inversion under quad workers.</p>
</body></html>"""

BOUNDARY_PART05 = """<!DOCTYPE html><html><body><h1>Stamp column</h1>
<p>Numeric stamp columns must sit on the aggregate that mutates during concurrent
replay. Header-only stamps do not guard line mutations.</p>
</body></html>"""

BOUNDARY_EXAMPLES = """<!DOCTYPE html><html><body><h1>Worked examples</h1>
<article id="ex4"><h2>Example 4</h2><p>Pool initializer downgrade breaks read-after-write snapshots.</p></article>
<article id="ex8"><h2>Example 8</h2><p>Second connection on a handoff observes phantom rollup without frame alignment.</p></article>
<article id="ex11"><h2>Example 11</h2><p>Post-success coordinator must run outside the ingest commit frame with its own transaction.</p></article>
</body></html>"""

DOCS = {
    "bench_precedence.md": """\
# Bench precedence

When operational playbooks disagree with the boundary contract corpus under
`/app/docs/boundary_contract/`, the boundary contract wins. Playbooks are
historical tuning notes only.

Resolution order:
1. Boundary contract HTML parts and worked examples
2. `operations_notes.md` (non-authoritative)
3. `ingest_pipeline.md` (transport overview)
""",
    "operations_notes.md": """\
# Operations notes

Teams often bump default transaction isolation on the pool or add pessimistic
locks on header repositories when parallel lane workers show drift. That can
flatten flakes on single-worker replays without fixing mixed-family counters.

Recommended experiments (often misleading):
- Raise ORM isolation property without touching pool initializer SQL
- Acquire `PESSIMISTIC_WRITE` on header repository before line inserts
- Disable Flyway in staging only

These changes are documented in `decoy/PessimisticAdvice.java` for review.
""",
    "ingest_pipeline.md": """\
# Lane pipeline overview

Workers POST JSON payloads to partition endpoints. The facility persists
header and line slices, maintains rollup counters via PL/pgSQL, and emits
post-success coordination events.

Audit harness: `/app/app/lane_audit.sh` writes `/app/output/lane_audit.json`.
""",
    "boundary_contract/glossary.md": """\
# Glossary

**Observation frame** — JDBC session semantics visible to readers within a transaction.

**Commit frame** — Unit of work ending at transaction commit.

**Slice lane** — Application persistence order for header and line aggregates.

**Rollup lane** — Database trigger path updating partition counters.

**Post-success envelope** — Coordinator work that must not re-enter the commit frame.
""",
    "boundary_contract/index.html": BOUNDARY_HTML_INDEX,
    "boundary_contract/part_02.html": BOUNDARY_PART02,
    "boundary_contract/part_03.html": BOUNDARY_PART03,
    "boundary_contract/part_04.html": BOUNDARY_PART04,
    "boundary_contract/part_05.html": BOUNDARY_PART05,
    "boundary_contract/examples.html": BOUNDARY_EXAMPLES,
}

TEST_OUTPUTS = '''"""Verifier for lane audit JSON."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output"
REPORT = OUT / "lane_audit.json"
AUDIT = APP / "app" / "lane_audit.sh"
ENSURE = APP / "init" / "ensure_pg.sh"
START = APP / "init" / "start_api.sh"

CAPS = {
    "North-Shelf": 6,
    "East-Crate": 10,
    "West-Bin": 4,
}
PARTITIONS = ["North-Shelf", "East-Crate", "West-Bin"]
SCENARIOS = (
    "w1_single",
    "w2_pair",
    "w4_quad",
    "mix_parallel",
    "deplete_exact",
    "pipe_backlog",
    "idempotent_rerun",
    "over_cap_reject",
    "interleave_ab",
    "partial_abort",
    "stamp_guard",
    "post_write_snap",
    "sibling_contention",
    "pool_dual_conn",
    "parity_probe",
    "biz_key_race",
    "rollup_seq_m",
    "rollup_seq_n",
    "rollup_seq_o",
    "rollup_seq_p",
    "tri_fanout",
    "solo_west",
)


def run_checked(cmd: list[str], *, timeout: int = 300) -> None:
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def run_audit() -> dict:
    run_checked(["bash", str(ENSURE)])
    run_checked(["bash", str(START)])
    OUT.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)], timeout=600)
    return json.loads(REPORT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


def test_v1_field(report: dict) -> None:
    assert report["schema_version"] == 1


def test_label_order(report: dict) -> None:
    assert report["catalog_partitions"] == PARTITIONS


def test_slots_complete(report: dict) -> None:
    for name in SCENARIOS:
        assert name in report["scenarios"]


def test_w1_single(report: dict) -> None:
    row = report["scenarios"]["w1_single"]
    assert row["lost_rows"] == 0
    assert row["chunks_attempted"] == 3


def test_w2_pair(report: dict) -> None:
    row = report["scenarios"]["w2_pair"]
    assert row["duplicate_external_keys"] == 0
    assert row["unstable_totals"] is False


def test_w4_quad(report: dict) -> None:
    row = report["scenarios"]["w4_quad"]
    assert row["unstable_totals"] is False


def test_mix_ok(report: dict) -> None:
    row = report["scenarios"]["mix_parallel"]
    assert row["unstable_totals"] is False


def test_deplete_ok(report: dict) -> None:
    row = report["scenarios"]["deplete_exact"]
    assert row["duplicate_external_keys"] == 0
    assert row["unstable_totals"] is False


def test_backlog_ok(report: dict) -> None:
    row = report["scenarios"]["pipe_backlog"]
    assert row["unstable_totals"] is False


def test_rerun_ok(report: dict) -> None:
    row = report["scenarios"]["idempotent_rerun"]
    assert row["duplicate_external_keys"] == 0


def test_cap_reject(report: dict) -> None:
    row = report["scenarios"]["over_cap_reject"]
    assert row["lost_rows"] == 0


def test_no_loss(report: dict) -> None:
    for name in SCENARIOS:
        assert report["scenarios"][name]["lost_rows"] == 0


def test_global_ok(report: dict) -> None:
    assert report["stress_summary"]["loss_events"] == 0


def test_interleave_ab(report: dict) -> None:
    row = report["scenarios"]["interleave_ab"]
    assert row["unstable_totals"] is False
    assert row["line_parity_ok"] is True


def test_partial_abort_ok(report: dict) -> None:
    row = report["scenarios"]["partial_abort"]
    assert row["line_parity_ok"] is True
    assert row["lost_rows"] == 0


def test_stamp_diverge_guard(report: dict) -> None:
    row = report["scenarios"]["stamp_guard"]
    assert row["duplicate_external_keys"] == 0


def test_snapshot_consistent(report: dict) -> None:
    row = report["scenarios"]["post_write_snap"]
    assert row["read_after_write_ok"] is True


def test_contention_sibling(report: dict) -> None:
    row = report["scenarios"]["sibling_contention"]
    assert row["unstable_totals"] is False


def test_pool_handoff_ok(report: dict) -> None:
    row = report["scenarios"]["pool_dual_conn"]
    assert row["unstable_totals"] is False


def test_line_parity_matrix(report: dict) -> None:
    for name in SCENARIOS:
        assert report["scenarios"][name]["line_parity_ok"] is True


def test_race_one_winner(report: dict) -> None:
    row = report["scenarios"]["biz_key_race"]
    assert row["duplicate_external_keys"] == 0


def test_monotone_counter(report: dict) -> None:
    for name in ("rollup_seq_m", "rollup_seq_n", "rollup_seq_o", "rollup_seq_p"):
        assert report["scenarios"][name]["rollup_monotone"] is True


def test_tri_fanout_ok(report: dict) -> None:
    row = report["scenarios"]["tri_fanout"]
    assert report["ingest_compliance"] or row["unstable_totals"] is False
    assert report["ingest_compliance"] is True
'''
