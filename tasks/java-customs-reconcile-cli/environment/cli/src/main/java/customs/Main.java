package customs;

import customs.app.EnrichCmd;
import customs.app.IngestCmd;
import customs.app.ReconcileCmd;

public final class Main {
  private Main() {}

  public static void main(String[] args) throws Exception {
    if (args.length < 2) {
      System.err.println("usage: customsctl <ingest|enrich|reconcile> <batch-id>");
      System.exit(2);
    }
    String verb = args[0];
    String batchId = args[1];
    switch (verb) {
      case "ingest" -> IngestCmd.run(batchId);
      case "enrich" -> EnrichCmd.run(batchId);
      case "reconcile" -> ReconcileCmd.run(batchId);
      default -> {
        System.err.println("unknown verb: " + verb);
        System.exit(2);
      }
    }
  }
}
