package meter.app;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import meter.ingest.NdjsonFetch;
import meter.util.JsonKit;
import meter.util.Paths;

public final class FetchCmd {
  private FetchCmd() {}

  public static void run(String a) throws Exception {
    List<Map<String, Object>> readings = NdjsonFetch.op_fetch_c(a);
    Map<String, Object> doc = new LinkedHashMap<>();
    doc.put("meter_id", a);
    doc.put("readings", readings);
    JsonKit.writeObject(Paths.READINGS_JSON, doc);
  }
}
