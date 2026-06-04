package meter.util;

import java.nio.file.Path;

public final class Paths {
  private Paths() {}

  public static final Path READINGS_JSON = Path.of("/app/var/readings.json");
  public static final Path NORMALIZED_JSON = Path.of("/app/var/normalized.json");
  public static final Path RECON_JSON = Path.of("/app/output/reconcile.json");
  public static final Path NORMALIZED_CSV = Path.of("/app/output/normalized.csv");
  public static final Path DEVICES_CSV = Path.of("/app/data/devices.csv");
  public static final Path TARIFFS_CSV = Path.of("/app/data/tariffs.csv");
  public static final String API_BASE = "http://127.0.0.1:8080";
}
