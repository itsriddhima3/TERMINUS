package trust.app;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import trust.parse.CertSlice;
import trust.parse.step_p4;
import trust.util.JsonKit;

public final class CorpusCmd {
  private CorpusCmd() {}

  public static void run(String[] args) throws Exception {
    Path matrix = Path.of("/app/data/cases/case_matrix.json");
    for (int i = 1; i < args.length - 1; i++) {
      if ("--matrix".equals(args[i])) {
        matrix = Path.of(args[i + 1]);
      }
    }
    Map<String, Object> root = JsonKit.readObject(matrix);
    List<Map<String, Object>> outCases = new ArrayList<>();
    for (Map<String, Object> row : JsonKit.objectList(root, "cases")) {
      String caseId = JsonKit.str(row, "case_id");
      Path pem = Path.of(JsonKit.str(row, "corpus_pem"));
      String anchor = JsonKit.str(row, "trust_anchor_cn");
      String leaf = JsonKit.str(row, "leaf_cn");
      List<CertSlice> slices = CertSlice.loadPemBundle(pem);
      List<String> chain = step_p4.fn_p4(slices, anchor, leaf);
      boolean akiOk = step_p4.aki_link_ok(slices, chain);
      Map<String, Object> entry = new LinkedHashMap<>();
      entry.put("case_id", caseId);
      entry.put("chain_cn", chain);
      boolean chainOk = step_p4.bench_chain_ok(chain, anchor, leaf);
      entry.put("chain_ok", chainOk);
      entry.put("aki_link_ok", akiOk);
      outCases.add(entry);
    }
    Map<String, Object> out = new LinkedHashMap<>();
    out.put("schema_version", 1);
    out.put("cases", outCases);
    JsonKit.writeObject(Path.of("/app/output/corpus_index.json"), out);
  }
}
