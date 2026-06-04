package customs.recon;

import customs.util.JsonKit;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ReportEmit {
  private ReportEmit() {}

  public record ReconBody(
      String batchId,
      List<String> underpaidLines,
      List<String> missingLines,
      Map<String, Double> exposureByImporter) {}

  /** Write reconcile JSON and CSV with stable ordering. */
  public static void op_emit_f(Path jsonOut, Path csvOut, ReconBody body) throws IOException {
    Map<String, Object> root = new LinkedHashMap<>();
    root.put("batch_id", body.batchId());
    root.put("underpaid_lines", body.underpaidLines());
    root.put("missing_classifications", body.missingLines());
    root.put("exposure_by_importer", body.exposureByImporter());
    JsonKit.writeObject(jsonOut, root);

    List<String> csvLines = new ArrayList<>();
    csvLines.add("line_id,importer_id,issue,exposure_usd");
    for (String lineId : body.underpaidLines()) {
      double exp = body.exposureByImporter().getOrDefault(lineId, 0.0);
      csvLines.add(lineId + ",,underpaid," + exp);
    }
    for (String lineId : body.missingLines()) {
      csvLines.add(lineId + ",,missing,0");
    }
    Files.createDirectories(csvOut.getParent());
    Files.write(csvOut, csvLines);
  }
}
