package customs.ingest;

import java.util.Locale;
import java.util.Map;

public final class CcyMap {
  private CcyMap() {}

  private static final Map<String, String> ALIASES =
      Map.of(
          "usd", "USD",
          "us$", "USD",
          "eur", "EUR",
          "gbp", "GBP",
          "jpy", "JPY");

  /** Map currency aliases to ISO uppercase tags. */
  public static String op_ccy_c(String raw) {
    String key = raw.trim().toLowerCase(Locale.ROOT);
    return ALIASES.getOrDefault(key, raw.trim());
  }
}
