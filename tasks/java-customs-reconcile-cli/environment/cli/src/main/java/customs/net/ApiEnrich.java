package customs.net;

import customs.ingest.CsvIngest;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class ApiEnrich {
  private ApiEnrich() {}

  public record ShipmentLine(
      String lineId,
      String importerId,
      String hs10,
      String currency,
      double declaredValue,
      double declaredDuty) {}

  public record EnrichedLine(
      String lineId,
      String importerId,
      String hs10,
      String currency,
      double declaredValue,
      double declaredDuty,
      Double tariffPct,
      Double fxToUsd,
      Boolean quotaBlocked,
      boolean classificationMissing) {}

  private static final Pattern NUM = Pattern.compile("-?\\d+(?:\\.\\d+)?");
  private static final Pattern BOOL = Pattern.compile("(true|false)");

  /** HTTP GET tariff, quota, and FX payloads for one line. */
  public static EnrichedLine op_query_d(int port, ShipmentLine line) throws Exception {
    Double tariffPct = null;
    Boolean quotaBlocked = null;
    boolean missing = false;

    String tariffBody = httpGet("http://127.0.0.1:" + port + "/api/v1/tariff/" + line.hs10());
    if (tariffBody.contains("not_found")) {
      missing = true;
    } else {
      Matcher m = Pattern.compile("\"rate_pct\"\\s*:\\s*").matcher(tariffBody);
      if (m.find()) {
        Matcher nm = NUM.matcher(tariffBody.substring(m.end()));
        if (nm.lookingAt()) tariffPct = Double.parseDouble(nm.group());
      }
    }

    if (!missing) {
      String quotaBody = httpGet("http://127.0.0.1:" + port + "/api/v1/quota/" + line.hs10());
      Matcher bm = BOOL.matcher(quotaBody);
      if (bm.find()) quotaBlocked = Boolean.parseBoolean(bm.group(1));
    }

    double fxToUsd = 1.0;
    String fxBody = httpGet("http://127.0.0.1:" + port + "/api/v1/fx/" + line.currency());
    Matcher fxm = Pattern.compile("\"fx_to_usd\"\\s*:\\s*").matcher(fxBody);
    if (fxm.find()) {
      Matcher nm = NUM.matcher(fxBody.substring(fxm.end()));
      if (nm.lookingAt()) {
        double raw = Double.parseDouble(nm.group());
        // Table stores USD-per-unit; enrichment divides to normalize.
        fxToUsd = raw == 0.0 ? 0.0 : 1.0 / raw;
      }
    }

    return new EnrichedLine(
        line.lineId(),
        line.importerId(),
        line.hs10(),
        line.currency(),
        line.declaredValue(),
        line.declaredDuty(),
        tariffPct,
        fxToUsd,
        quotaBlocked,
        missing);
  }

  private static String httpGet(String urlStr) throws Exception {
    URL url = new URL(urlStr);
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    conn.setRequestMethod("GET");
    conn.setConnectTimeout(5000);
    conn.setReadTimeout(5000);
    int code = conn.getResponseCode();
    BufferedReader br =
        new BufferedReader(
            new InputStreamReader(
                code >= 400 ? conn.getErrorStream() : conn.getInputStream(),
                StandardCharsets.UTF_8));
    StringBuilder sb = new StringBuilder();
    String line;
    while ((line = br.readLine()) != null) sb.append(line);
    return sb.toString();
  }
}
