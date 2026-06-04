package customs.app;

import customs.net.ApiEnrich;
import customs.recon.DutyCalc;
import customs.recon.ReportEmit;
import customs.util.JsonKit;
import customs.util.PolicyLoad;
import customs.util.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

@SuppressWarnings("unchecked")
public final class ReconcileCmd {
  private ReconcileCmd() {}

  public static void run(String batchId) throws Exception {
    Map<String, Object> doc = JsonKit.readObject(Paths.ENRICHED_JSON);
    double tolerance = 0.01;
    List<String> underpaid = new ArrayList<>();
    List<String> missing = new ArrayList<>();
    Map<String, Double> exposure = new TreeMap<>();

    List<Map<String, Object>> rows = (List<Map<String, Object>>) doc.get("lines");
    for (Map<String, Object> row : rows) {
      ApiEnrich.EnrichedLine line =
          new ApiEnrich.EnrichedLine(
              (String) row.get("line_id"),
              (String) row.get("importer_id"),
              (String) row.get("hs10"),
              (String) row.get("currency"),
              ((Number) row.get("declared_value")).doubleValue(),
              ((Number) row.get("declared_duty")).doubleValue(),
              row.get("tariff_pct") == null ? null : ((Number) row.get("tariff_pct")).doubleValue(),
              ((Number) row.get("fx_to_usd")).doubleValue(),
              row.get("quota_blocked") == null ? null : (Boolean) row.get("quota_blocked"),
              Boolean.TRUE.equals(row.get("classification_missing")));

      if (line.classificationMissing()) {
        missing.add(line.lineId());
        continue;
      }
      if (DutyCalc.isUnderpaid(line, tolerance)) {
        underpaid.add(line.lineId());
      }
      exposure.merge(line.importerId(), line.declaredDuty(), Double::sum);
    }

    ReportEmit.ReconBody body =
        new ReportEmit.ReconBody(batchId, underpaid, missing, exposure);
    ReportEmit.op_emit_f(Paths.RECON_JSON, Paths.RECON_CSV, body);
  }
}
