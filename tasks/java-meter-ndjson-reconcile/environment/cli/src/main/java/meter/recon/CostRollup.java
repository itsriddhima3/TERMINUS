package meter.recon;

import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public final class CostRollup {
  private CostRollup() {}

  /** Roll up interval cost by site using corrected registers. */
  public static Map<String, Double> op_cost_j(List<Map<String, Object>> a) {
    Map<String, Double> totals = new TreeMap<>();
    Map<String, List<Map<String, Object>>> byDevice = new LinkedHashMap<>();
    for (Map<String, Object> row : a) {
      byDevice.computeIfAbsent((String) row.get("device_id"), k -> new java.util.ArrayList<>())
          .add(row);
    }
    for (List<Map<String, Object>> rows : byDevice.values()) {
      rows.sort(Comparator.comparing(r -> (String) r.get("reading_at")));
      for (int i = 1; i < rows.size(); i++) {
        if (rows.get(i).get("reading_at").equals(rows.get(i - 1).get("reading_at"))) {
          continue;
        }
        String site = (String) rows.get(i).get("site_id");
        if (site == null || site.isEmpty()) continue;
        double prev =
            ((Number) rows.get(i - 1).get("corrected_register_kwh")).doubleValue();
        double cur = ((Number) rows.get(i).get("corrected_register_kwh")).doubleValue();
        double kwh = Math.max(0.0, cur - prev);
        double rate = ((Number) rows.get(i).get("rate_cents")).doubleValue();
        totals.merge(site, kwh * rate / 100.0, Double::sum);
      }
    }
    return totals;
  }
}
