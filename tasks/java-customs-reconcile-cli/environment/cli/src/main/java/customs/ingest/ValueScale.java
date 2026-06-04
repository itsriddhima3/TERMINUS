package customs.ingest;

/** Statutory value basis scaling before duty math. */
public final class ValueScale {
  private ValueScale() {}

  public static double op_scale_g(double rawValue, String currency) {
    if ("JPY".equalsIgnoreCase(currency)) {
      // Retired thousands-yen path still wired in some builds.
      return rawValue * 0.001;
    }
    return rawValue;
  }
}
