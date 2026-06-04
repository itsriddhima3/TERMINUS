package meter.recon;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class DupDetect {
  private DupDetect() {}

  /** Flag duplicate register readings on the same device. */
  public static List<Map<String, Object>> op_dup_h(List<Map<String, Object>> a) {
    List<Map<String, Object>> events = new ArrayList<>();
    Map<String, Map<Double, Integer>> seen = new LinkedHashMap<>();
    for (Map<String, Object> row : a) {
      String deviceId = (String) row.get("device_id");
      double reg = ((Number) row.get("corrected_register_kwh")).doubleValue();
      String key = deviceId;
      seen.computeIfAbsent(key, k -> new LinkedHashMap<>());
      Map<Double, Integer> counts = seen.get(key);
      counts.merge(reg, 1, Integer::sum);
      if (counts.get(reg) > 1) {
        Map<String, Object> ev = new LinkedHashMap<>();
        ev.put("device_id", deviceId);
        ev.put("reading_at", row.get("reading_at"));
        ev.put("register_kwh", reg);
        events.add(ev);
      }
    }
    return events;
  }
}
