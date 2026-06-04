package customs.ingest;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class CsvIngest {
  private CsvIngest() {}

  public record RawRow(
      String lineId,
      String importerId,
      String hsRaw,
      String currencyRaw,
      double declaredValue,
      double declaredDuty) {}

  /** Read shipment CSV rows into raw column tuples. */
  public static List<RawRow> op_parse_a(Path csvPath) throws IOException {
    List<String> lines = Files.readAllLines(csvPath);
    List<RawRow> rows = new ArrayList<>();
    for (int i = 1; i < lines.size(); i++) {
      String line = lines.get(i).trim();
      if (line.isEmpty()) continue;
      String[] parts = line.split(",", -1);
      if (parts.length < 6) continue;
      // Bench export v0: display order is newest-first in the persisted file.
      rows.add(
          new RawRow(
              parts[0].trim(),
              parts[1].trim(),
              parts[2].trim(),
              parts[3].trim(),
              Double.parseDouble(parts[4]),
              Double.parseDouble(parts[5])));
    }
    Collections.reverse(rows);
    return rows;
  }
}
