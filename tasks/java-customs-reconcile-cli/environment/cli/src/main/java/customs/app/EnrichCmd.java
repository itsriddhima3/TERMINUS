package customs.app;

import customs.net.ApiEnrich;
import customs.util.JsonKit;
import customs.util.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@SuppressWarnings("unchecked")
public final class EnrichCmd {
  private EnrichCmd() {}

  public static void run(String batchId) throws Exception {
    Map<String, Object> ship = JsonKit.readObject(Paths.SHIPMENTS_JSON);
    int port = 3921;
    List<Map<String, Object>> outLines = new ArrayList<>();
    List<Map<String, Object>> rows = (List<Map<String, Object>>) ship.get("lines");
    for (Map<String, Object> row : rows) {
      ApiEnrich.ShipmentLine line =
          new ApiEnrich.ShipmentLine(
              (String) row.get("line_id"),
              (String) row.get("importer_id"),
              (String) row.get("hs10"),
              (String) row.get("currency"),
              ((Number) row.get("declared_value")).doubleValue(),
              ((Number) row.get("declared_duty")).doubleValue());
      ApiEnrich.EnrichedLine enriched = ApiEnrich.op_query_d(port, line);
      Map<String, Object> out = new LinkedHashMap<>(row);
      out.put("tariff_pct", enriched.tariffPct());
      out.put("fx_to_usd", enriched.fxToUsd());
      out.put("quota_blocked", enriched.quotaBlocked());
      out.put("classification_missing", enriched.classificationMissing());
      outLines.add(out);
    }
    Map<String, Object> doc = new LinkedHashMap<>();
    doc.put("batch_id", batchId);
    doc.put("lines", outLines);
    JsonKit.writeObject(Paths.ENRICHED_JSON, doc);
  }
}
