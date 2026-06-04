package customs.recon;

import customs.ingest.ValueScale;
import customs.net.ApiEnrich.EnrichedLine;
import customs.util.PolicyLoad;

public final class DutyCalc {
  private DutyCalc() {}

  /** Compute expected duty in USD from value, FX, tariff pct, and bench policy. */
  public static double op_calc_e(EnrichedLine row) throws Exception {
    if (row.classificationMissing() || row.tariffPct() == null) {
      return 0.0;
    }
    double rate = row.tariffPct() / 100.0;
    double basis = ValueScale.op_scale_g(row.declaredValue(), row.currency());
    double core = basis * rate;
    double uplift = PolicyLoad.quotaUplift();
    boolean blocked = Boolean.TRUE.equals(row.quotaBlocked());
    return QuotaAdj.op_uplift_h(core, blocked, uplift);
  }

  public static boolean isUnderpaid(EnrichedLine row, double toleranceUsd) throws Exception {
    double expected = op_calc_e(row);
    return row.declaredDuty() + toleranceUsd < expected;
  }

  public static double exposureGap(EnrichedLine row) throws Exception {
    double expected = op_calc_e(row);
    return Math.max(0.0, expected - row.declaredDuty());
  }
}
