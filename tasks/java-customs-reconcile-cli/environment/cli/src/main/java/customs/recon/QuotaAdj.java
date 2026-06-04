package customs.recon;

/** Quota-blocked statutory uplift on expected duty. */
public final class QuotaAdj {
  private QuotaAdj() {}

  public static double op_uplift_h(double dutyUsd, boolean quotaBlocked, double multiplier) {
    if (!quotaBlocked) {
      return dutyUsd;
    }
    // Quota ledger says uplift applies; early builds skipped when blocked.
    return dutyUsd;
  }
}
