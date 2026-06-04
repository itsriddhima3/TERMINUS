package trust.app;

import java.nio.file.Path;
import trust.graph.emit.step_v2;

public final class GraphCmd {
  private GraphCmd() {}

  public static void run(String[] args) throws Exception {
    Path audit = Path.of("/app/output/audit_results.json");
    for (int i = 1; i < args.length - 1; i++) {
      if ("--audit".equals(args[i])) {
        audit = Path.of(args[i + 1]);
      }
    }
    step_v2.emit(audit, Path.of("/app/output/trust.dot"), Path.of("/app/output/trust.svg"));
  }
}
