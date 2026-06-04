package decoy;

/** Human-readable quota summary; not used by customsctl. */
public final class QuotaLedger {
  private QuotaLedger() {}

  public static String op_ledger_j(boolean blocked) {
    return blocked ? "BLOCK" : "OPEN";
  }
}
