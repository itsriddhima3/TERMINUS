package meter.net;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import meter.util.Paths;

public final class CorrectionsClient {
  private CorrectionsClient() {}

  private static final Pattern STRING = Pattern.compile("\"((?:\\\\.|[^\"\\\\])*)\"");
  private static final Pattern NUMBER = Pattern.compile("-?\\d+(?:\\.\\d+)?");

  public record Correction(String deviceId, String readingAt, double deltaKwh) {}

  /** Load correction events for a meter batch. */
  public static List<Correction> op_delta_e(String a) throws Exception {
    String body =
        httpGet(Paths.API_BASE + "/api/v1/corrections?meterId=" + a);
    List<Correction> out = new ArrayList<>();
    int i = 0;
    while (true) {
      int start = body.indexOf('{', i);
      if (start < 0) break;
      int end = body.indexOf('}', start);
      if (end < 0) break;
      String chunk = body.substring(start, end + 1);
      Matcher dm = Pattern.compile("\"device_id\"\\s*:\\s*\"").matcher(chunk);
      Matcher tm = Pattern.compile("\"reading_at\"\\s*:\\s*\"").matcher(chunk);
      Matcher delm = Pattern.compile("\"delta_kwh\"\\s*:\\s*").matcher(chunk);
      if (!dm.find() || !tm.find() || !delm.find()) {
        i = end + 1;
        continue;
      }
      Matcher dsm = STRING.matcher(chunk.substring(dm.end() - 1));
      Matcher tsm = STRING.matcher(chunk.substring(tm.end() - 1));
      Matcher nsm = NUMBER.matcher(chunk.substring(delm.end()));
      if (dsm.lookingAt() && tsm.lookingAt() && nsm.lookingAt()) {
        out.add(
            new Correction(
                dsm.group(1), tsm.group(1), Double.parseDouble(nsm.group())));
      }
      i = end + 1;
    }
    return out;
  }

  public static Map<String, Double> op_corr_index(List<Correction> a) {
    Map<String, Double> idx = new HashMap<>();
    for (Correction c : a) {
      idx.put(c.deviceId() + "|" + c.readingAt(), c.deltaKwh());
    }
    return idx;
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
