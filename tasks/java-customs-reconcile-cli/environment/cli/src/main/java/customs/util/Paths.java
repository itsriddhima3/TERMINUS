package customs.util;

import java.nio.file.Path;

public final class Paths {
  private Paths() {}

  public static final Path RUNTIME = Path.of("/app/platform/runtime.json");
  public static final Path SHIPMENTS_JSON = Path.of("/app/var/shipments.json");
  public static final Path ENRICHED_JSON = Path.of("/app/var/enriched.json");
  public static final Path RECON_JSON = Path.of("/app/output/reconcile.json");
  public static final Path RECON_CSV = Path.of("/app/output/reconcile.csv");

  public static Path csvForBatch(String batchId) {
    return Path.of("/app/data/shipments", batchId + ".csv");
  }
}
