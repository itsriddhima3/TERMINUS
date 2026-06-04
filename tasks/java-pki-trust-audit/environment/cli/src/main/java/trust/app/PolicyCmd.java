package trust.app;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import trust.parse.CertSlice;
import trust.parse.step_p4;
import trust.policy.RevTable;
import trust.policy.op_k7;
import trust.util.JsonKit;

public final class PolicyCmd {
  private PolicyCmd() {}

  public static void run(String[] args) throws Exception {
    Path matrix = Path.of("/app/data/cases/case_matrix.json");
    Path corpus = Path.of("/app/output/corpus_index.json");
    for (int i = 1; i < args.length - 1; i++) {
      if ("--matrix".equals(args[i])) {
        matrix = Path.of(args[i + 1]);
      } else if ("--corpus".equals(args[i])) {
        corpus = Path.of(args[i + 1]);
      }
    }
    Map<String, Object> matrixRoot = JsonKit.readObject(matrix);
    String evalInstant = JsonKit.str(matrixRoot, "eval_instant");
    Map<String, Object> corpusRoot = JsonKit.readObject(corpus);
    Map<String, Map<String, Object>> corpusById = new LinkedHashMap<>();
    for (Map<String, Object> c : JsonKit.objectList(corpusRoot, "cases")) {
      corpusById.put(JsonKit.str(c, "case_id"), c);
    }
    List<Map<String, Object>> outCases = new ArrayList<>();
    for (Map<String, Object> row : JsonKit.objectList(matrixRoot, "cases")) {
      String caseId = JsonKit.str(row, "case_id");
      Map<String, Object> corpusRow = corpusById.get(caseId);
      @SuppressWarnings("unchecked")
      List<String> chain = (List<String>) corpusRow.get("chain_cn");
      Path pem = Path.of(JsonKit.str(row, "corpus_pem"));
      List<CertSlice> slices = CertSlice.loadPemBundle(pem);
      RevTable rev = RevTable.empty();
      String crlGlob = JsonKit.str(row, "crl_glob");
      if (crlGlob != null) {
        rev = RevTable.mergeGlob(crlGlob);
      }
      String reason;
      if (chain == null || chain.isEmpty()) {
        reason = "parse_fail";
      } else {
        reason = op_k7.apply(row, slices, chain, rev, evalInstant);
      }
      String verdict = "accept".equals(reason) ? "accept" : "reject";
      Map<String, Object> entry = new LinkedHashMap<>();
      entry.put("case_id", caseId);
      entry.put("verdict", verdict);
      entry.put("reason", "accept".equals(reason) ? null : reason);
      entry.put("chain_cn", chain);
      outCases.add(entry);
    }
    Map<String, Object> out = new LinkedHashMap<>();
    out.put("schema_version", 1);
    out.put("cases", outCases);
    JsonKit.writeObject(Path.of("/app/output/audit_results.json"), out);
  }
}
