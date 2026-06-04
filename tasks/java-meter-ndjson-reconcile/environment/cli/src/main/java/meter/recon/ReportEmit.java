package meter.recon;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import meter.util.JsonKit;

public final class ReportEmit {
  private ReportEmit() {}

  public record ReconBody(
      String meterId,
      List<Map<String, Object>> gapEvents,
      List<Map<String, Object>> duplicateEvents,
      List<Map<String, Object>> impossibleDeltaEvents,
      Map<String, Double> costBySite) {}

  public static void op_emit_k(
      Path jsonOut, Path csvOut, ReconBody a, List<Map<String, Object>> b) throws IOException {
    Map<String, Object> root = new LinkedHashMap<>();
    root.put("meter_id", a.meterId());
    root.put("gap_events", a.gapEvents());
    root.put("duplicate_events", a.duplicateEvents());
    root.put("impossible_delta_events", a.impossibleDeltaEvents());
    root.put("cost_by_site", a.costBySite());
    JsonKit.writeObject(jsonOut, root);

    Set<String> gapKeys = new HashSet<>();
    for (Map<String, Object> ev : a.gapEvents()) {
      gapKeys.add(ev.get("device_id") + "|" + ev.get("expected_at"));
    }
    Set<String> dupKeys = new HashSet<>();
    for (Map<String, Object> ev : a.duplicateEvents()) {
      dupKeys.add(ev.get("device_id") + "|" + ev.get("reading_at"));
    }
    Set<String> deltaKeys = new HashSet<>();
    for (Map<String, Object> ev : a.impossibleDeltaEvents()) {
      deltaKeys.add(ev.get("device_id") + "|" + ev.get("reading_at"));
    }

    List<String> lines = new ArrayList<>();
    lines.add("device_id,reading_at,register_kwh,site_id,rate_cents,issue");
    for (Map<String, Object> row : b) {
      String deviceId = (String) row.get("device_id");
      String readingAt = (String) row.get("reading_at");
      String key = deviceId + "|" + readingAt;
      String issue = "";
      if (gapKeys.contains(key)) issue = "gap";
      else if (dupKeys.contains(key)) issue = "duplicate";
      else if (deltaKeys.contains(key)) issue = "impossible_delta";
      lines.add(
          deviceId
              + ","
              + readingAt
              + ","
              + row.get("register_kwh")
              + ","
              + row.get("site_id")
              + ","
              + row.get("rate_cents")
              + ","
              + issue);
    }
    Files.createDirectories(csvOut.getParent());
    Files.write(csvOut, lines);
  }
}
