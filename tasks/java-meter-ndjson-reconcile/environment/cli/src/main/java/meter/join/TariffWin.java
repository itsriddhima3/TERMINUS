package meter.join;

import java.util.List;
import meter.ingest.CsvLookup.TariffRow;

public final class TariffWin {
  private TariffWin() {}

  /** Resolve rate_cents for a site and clock time (HH:mm). */
  public static double op_tariff_f(List<TariffRow> a, String b, String c) {
    if (a.isEmpty()) return 0.0;
    for (TariffRow row : a) {
      if (!row.siteId().equals(b)) continue;
      if (c.compareTo(row.windowStart()) >= 0 && c.compareTo(row.windowEnd()) <= 0) {
        return row.rateCents();
      }
    }
    return a.get(0).rateCents();
  }

  public static String op_clock_g(String a) {
    int t = a.indexOf('T');
    if (t < 0) return "00:00";
    String tail = a.substring(t + 1);
    if (tail.length() >= 5) return tail.substring(0, 5);
    return tail;
  }
}
