package meter.recon;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class DeltaCheck {
  private DeltaCheck() {}

  /** Compare consecutive register deltas against device limits. */
  public static List<Map<String, Object>> op_delta_i(List<Map<String, Object>> a) {
    List<Map<String, Object>> events = new ArrayList<>();
    Map<String, List<Map<String, Object>>> byDevice = new LinkedHashMap<>();
    for (Map<String, Object> row : a) {
      byDevice.computeIfAbsent((String) row.get("device_id"), k -> new ArrayList<>()).add(row);
    }
    for (Map.Entry<String, List<Map<String, Object>>> entry : byDevice.entrySet()) {
      List<Map<String, Object>> rows = entry.getValue();
      rows.sort(Comparator.comparing(r -> (String) r.get("reading_at")));
      for (int i = 1; i < rows.size(); i++) {
        double prev = ((Number) rows.get(i - 1).get("register_kwh")).doubleValue();
        double cur = ((Number) rows.get(i).get("register_kwh")).doubleValue();
        double delta = cur - prev;
        double limit = ((Number) rows.get(i).get("max_delta_kwh_per_interval")).doubleValue();
        if (limit > 0 && delta > limit + 10.0) {
          Map<String, Object> ev = new LinkedHashMap<>();
          ev.put("device_id", entry.getKey());
          ev.put("reading_at", rows.get(i).get("reading_at"));
          ev.put("delta_kwh", delta);
          ev.put("max_delta_kwh_per_interval", limit);
          events.add(ev);
        }
      }
    }
    return events;
  }
}
