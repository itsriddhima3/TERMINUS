package meter.ingest;

public final class TsNorm {
  private TsNorm() {}

  /** Normalize ISO8601 reading timestamps for persistence. */
  public static String op_norm_b(String a) {
    if (a.endsWith("Z")) {
      return a.substring(0, a.length() - 1);
    }
    return a;
  }
}
