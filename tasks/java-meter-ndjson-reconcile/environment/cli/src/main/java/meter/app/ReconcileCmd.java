package meter.app;

import java.util.List;
import java.util.Map;
import meter.recon.CostRollup;
import meter.recon.DeltaCheck;
import meter.recon.DupDetect;
import meter.recon.GapDetect;
import meter.recon.ReportEmit;
import meter.recon.ReportEmit.ReconBody;
import meter.util.JsonKit;
import meter.util.PolicyLoad;
import meter.util.Paths;

@SuppressWarnings("unchecked")
public final class ReconcileCmd {
  private ReconcileCmd() {}

  public static void run(String a) throws Exception {
    Map<String, Object> doc = JsonKit.readObject(Paths.NORMALIZED_JSON);
    List<Map<String, Object>> readings = (List<Map<String, Object>>) doc.get("readings");
    int gapTol = PolicyLoad.gapToleranceMin();

    List<Map<String, Object>> gaps = GapDetect.op_gap_g(readings, gapTol);
    List<Map<String, Object>> dups = DupDetect.op_dup_h(readings);
    List<Map<String, Object>> deltas = DeltaCheck.op_delta_i(readings);
    Map<String, Double> costBySite = CostRollup.op_cost_j(readings);

    ReconBody body =
        new ReconBody(a, gaps, dups, deltas, costBySite);
    ReportEmit.op_emit_k(Paths.RECON_JSON, Paths.NORMALIZED_CSV, body, readings);
  }
}
