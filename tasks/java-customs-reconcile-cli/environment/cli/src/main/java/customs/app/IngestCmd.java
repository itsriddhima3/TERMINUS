package customs.app;

import customs.ingest.CcyMap;
import customs.ingest.CsvIngest;
import customs.ingest.HsFold;
import customs.util.JsonKit;
import customs.util.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class IngestCmd {
  private IngestCmd() {}

  public static void run(String batchId) throws Exception {
    List<CsvIngest.RawRow> raw = CsvIngest.op_parse_a(Paths.csvForBatch(batchId));
    List<Map<String, Object>> lines = new ArrayList<>();
    for (CsvIngest.RawRow row : raw) {
      Map<String, Object> line = new LinkedHashMap<>();
      line.put("line_id", row.lineId());
      line.put("importer_id", row.importerId());
      line.put("hs10", HsFold.op_norm_b(row.hsRaw()));
      line.put("currency", CcyMap.op_ccy_c(row.currencyRaw()));
      line.put("declared_value", row.declaredValue());
      line.put("declared_duty", row.declaredDuty());
      lines.add(line);
    }
    Map<String, Object> doc = new LinkedHashMap<>();
    doc.put("batch_id", batchId);
    doc.put("lines", lines);
    JsonKit.writeObject(Paths.SHIPMENTS_JSON, doc);
  }
}
