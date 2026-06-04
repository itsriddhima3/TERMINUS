package meter.ingest;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class CsvLookup {
  private CsvLookup() {}

  public record DeviceRow(String deviceId, String siteId, double maxDelta) {}

  public record TariffRow(String siteId, String windowStart, String windowEnd, double rateCents) {}

  public static Map<String, DeviceRow> op_join_d(Path a) throws IOException {
    List<String> lines = Files.readAllLines(a);
    Map<String, DeviceRow> index = new HashMap<>();
    for (int i = 1; i < lines.size(); i++) {
      String line = lines.get(i).trim();
      if (line.isEmpty()) continue;
      String[] parts = line.split(",", -1);
      if (parts.length < 3) continue;
      DeviceRow row =
          new DeviceRow(
              parts[0].trim(),
              parts[1].trim(),
              Double.parseDouble(parts[2].trim()));
      index.put(row.siteId(), row);
    }
    return index;
  }

  public static List<TariffRow> op_rate_e(Path a) throws IOException {
    List<String> lines = Files.readAllLines(a);
    List<TariffRow> rows = new ArrayList<>();
    for (int i = 1; i < lines.size(); i++) {
      String line = lines.get(i).trim();
      if (line.isEmpty()) continue;
      String[] parts = line.split(",", -1);
      if (parts.length < 4) continue;
      rows.add(
          new TariffRow(
              parts[0].trim(),
              parts[1].trim(),
              parts[2].trim(),
              Double.parseDouble(parts[3].trim())));
    }
    return rows;
  }
}
