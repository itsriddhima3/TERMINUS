package meter.recon;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class GapDetect {
  private GapDetect() {}

  /** Detect missing interval slots per device. */
  public static List<Map<String, Object>> op_gap_g(List<Map<String, Object>> a, int b) {
    List<Map<String, Object>> events = new ArrayList<>();
    Map<String, List<Map<String, Object>>> byDevice = new LinkedHashMap<>();
    for (Map<String, Object> row : a) {
      String deviceId = (String) row.get("device_id");
      byDevice.computeIfAbsent(deviceId, k -> new ArrayList<>()).add(row);
    }
    for (Map.Entry<String, List<Map<String, Object>>> entry : byDevice.entrySet()) {
      List<Map<String, Object>> rows = entry.getValue();
      rows.sort(Comparator.comparing(r -> (String) r.get("reading_at")));
      for (int i = 1; i < rows.size(); i++) {
        int prevMin = intervalMin(rows.get(i - 1));
        int gapMin = minutesBetween((String) rows.get(i - 1).get("reading_at"),
            (String) rows.get(i).get("reading_at"));
        if (gapMin > b * 2) {
          Map<String, Object> ev = new LinkedHashMap<>();
          ev.put("device_id", entry.getKey());
          ev.put("expected_at", rows.get(i).get("reading_at"));
          ev.put("gap_minutes", gapMin - prevMin);
          events.add(ev);
        }
      }
    }
    return events;
  }

  private static int intervalMin(Map<String, Object> row) {
    Object v = row.get("interval_min");
    return v == null ? 15 : ((Number) v).intValue();
  }

  private static int minutesBetween(String a, String b) {
    int ma = clockMinutes(a);
    int mb = clockMinutes(b);
    return Math.abs(mb - ma);
  }

  private static int clockMinutes(String ts) {
    int t = ts.indexOf('T');
    String tail = t >= 0 ? ts.substring(t + 1) : ts;
    String[] parts = tail.split(":");
    int h = parts.length > 0 ? Integer.parseInt(parts[0]) : 0;
    int m = parts.length > 1 ? Integer.parseInt(parts[1]) : 0;
    return h * 60 + m;
  }
}
