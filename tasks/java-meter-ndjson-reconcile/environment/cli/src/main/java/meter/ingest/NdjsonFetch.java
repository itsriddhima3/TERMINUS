package meter.ingest;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import meter.util.Paths;

public final class NdjsonFetch {
  private NdjsonFetch() {}

  private static final Pattern STRING = Pattern.compile("\"((?:\\\\.|[^\"\\\\])*)\"");
  private static final Pattern NUMBER = Pattern.compile("-?\\d+(?:\\.\\d+)?");

  /** Pull one NDJSON page from the readings stream endpoint. */
  public static List<Map<String, Object>> op_fetch_c(String a) throws Exception {
    List<Map<String, Object>> out = new ArrayList<>();
    String body = httpGet(Paths.API_BASE + "/api/v1/readings/stream?meterId=" + a + "&cursor=");
    for (String line : body.split("\n")) {
      String trimmed = line.trim();
      if (trimmed.isEmpty()) continue;
      out.add(op_parse_a(trimmed));
    }
    Collections.reverse(out);
    return out;
  }

  /** Parse a single NDJSON object line into a reading map. */
  public static Map<String, Object> op_parse_a(String b) {
    Map<String, Object> row = new LinkedHashMap<>();
    Matcher dm = Pattern.compile("\"device_id\"\\s*:\\s*\"").matcher(b);
    if (dm.find()) {
      Matcher sm = STRING.matcher(b.substring(dm.end() - 1));
      if (sm.lookingAt()) row.put("device_id", sm.group(1));
    }
    Matcher tm = Pattern.compile("\"reading_at\"\\s*:\\s*\"").matcher(b);
    if (tm.find()) {
      Matcher sm = STRING.matcher(b.substring(tm.end() - 1));
      if (sm.lookingAt()) row.put("reading_at", TsNorm.op_norm_b(sm.group(1)));
    }
    Matcher rm = Pattern.compile("\"register_kwh\"\\s*:\\s*").matcher(b);
    if (rm.find()) {
      Matcher nm = NUMBER.matcher(b.substring(rm.end()));
      if (nm.lookingAt()) row.put("register_kwh", Double.parseDouble(nm.group()));
    }
    Matcher im = Pattern.compile("\"interval_min\"\\s*:\\s*").matcher(b);
    if (im.find()) {
      Matcher nm = NUMBER.matcher(b.substring(im.end()));
      if (nm.lookingAt()) row.put("interval_min", Integer.parseInt(nm.group()));
    }
    return row;
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
    while ((line = br.readLine()) != null) {
      if (!sb.isEmpty()) sb.append('\n');
      sb.append(line);
    }
    return sb.toString();
  }
}
