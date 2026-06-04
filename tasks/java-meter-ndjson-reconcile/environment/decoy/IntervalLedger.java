package decoy;

/** Human-readable interval summary; not used by meterctl. */
public final class IntervalLedger {
  private IntervalLedger() {}

  public static String op_ledger_j(int intervalMin) {
    return intervalMin == 15 ? "QUARTER" : "CUSTOM";
  }
}
