package meter.app;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import meter.ingest.CsvLookup;
import meter.ingest.CsvLookup.DeviceRow;
import meter.ingest.CsvLookup.TariffRow;
import meter.join.TariffWin;
import meter.net.CorrectionsClient;
import meter.net.CorrectionsClient.Correction;
import meter.util.JsonKit;
import meter.util.Paths;

@SuppressWarnings("unchecked")
public final class NormalizeCmd {
  private NormalizeCmd() {}

  public static void run(String a) throws Exception {
    Map<String, Object> src = JsonKit.readObject(Paths.READINGS_JSON);
    Map<String, DeviceRow> devices = CsvLookup.op_join_d(Paths.DEVICES_CSV);
    List<TariffRow> tariffs = CsvLookup.op_rate_e(Paths.TARIFFS_CSV);
    List<Correction> corrections = CorrectionsClient.op_delta_e(a);
    Map<String, Double> corrIdx = CorrectionsClient.op_corr_index(corrections);
    Set<String> ledgerApplied = new HashSet<>();

    List<Map<String, Object>> enriched = new ArrayList<>();
    List<Map<String, Object>> readings = (List<Map<String, Object>>) src.get("readings");
    for (Map<String, Object> row : readings) {
      String deviceId = (String) row.get("device_id");
      String readingAt = (String) row.get("reading_at");
      double register = ((Number) row.get("register_kwh")).doubleValue();
      int intervalMin =
          row.get("interval_min") == null
              ? 15
              : ((Number) row.get("interval_min")).intValue();

      DeviceRow dev = devices.get(deviceId);
      String siteId = dev == null ? "" : dev.siteId();
      double maxDelta = dev == null ? 0.0 : dev.maxDelta();
      String clock = TariffWin.op_clock_g(readingAt);
      double rateCents = TariffWin.op_tariff_f(tariffs, siteId, clock);

      double corrected = register;
      String corrKey = deviceId + "|" + readingAt;
      if (corrIdx.containsKey(corrKey) && !ledgerApplied.contains(corrKey)) {
        corrected = register + corrIdx.get(corrKey);
        ledgerApplied.add(corrKey);
      }

      Map<String, Object> out = new LinkedHashMap<>(row);
      out.put("site_id", siteId);
      out.put("rate_cents", rateCents);
      out.put("max_delta_kwh_per_interval", maxDelta);
      out.put("corrected_register_kwh", corrected);
      out.put("interval_min", intervalMin);
      enriched.add(out);
    }

    Map<String, Object> doc = new LinkedHashMap<>();
    doc.put("meter_id", a);
    doc.put("readings", enriched);
    JsonKit.writeObject(Paths.NORMALIZED_JSON, doc);
  }
}
