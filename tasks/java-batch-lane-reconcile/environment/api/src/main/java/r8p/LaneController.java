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
