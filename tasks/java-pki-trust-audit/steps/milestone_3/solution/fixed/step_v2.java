package trust.graph.emit;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import trust.util.JsonKit;

public final class step_v2 {
  private step_v2() {}

  public static void emit(Path auditPath, Path dotPath, Path svgPath) throws Exception {
    Map<String, Object> audit = JsonKit.readObject(auditPath);
    List<Map<String, Object>> cases = JsonKit.objectList(audit, "cases");
    StringBuilder dot = new StringBuilder("digraph trust {\n  rankdir=TB;\n");
    List<String> edges = new ArrayList<>();
    for (Map<String, Object> row : cases) {
      String caseId = JsonKit.str(row, "case_id");
      String verdict = JsonKit.str(row, "verdict");
      String reason = JsonKit.str(row, "reason");
      @SuppressWarnings("unchecked")
      List<String> chain = (List<String>) row.get("chain_cn");
      if (chain == null) {
        continue;
      }
      for (int i = 0; i < chain.size(); i++) {
        String cn = chain.get(i);
        String nodeId = sanitize(cn + "_" + caseId);
        String role = roleFor(i, chain.size(), verdict, reason);
        Map<String, String> attrs = StyleLedger.attrsFor(role);
        dot.append("  ").append(nodeId).append(" [label=\"").append(cn).append("\"");
        for (Map.Entry<String, String> e : attrs.entrySet()) {
          dot.append(" ").append(e.getKey()).append("=\"").append(e.getValue()).append("\"");
        }
        dot.append("];\n");
        if (i > 0) {
          String parent = sanitize(chain.get(i - 1) + "_" + caseId);
          String edgeColor = "accept".equals(verdict) ? "forestgreen" : "gray";
          edges.add("  " + parent + " -> " + nodeId + " [color=" + edgeColor + "];\n");
        }
      }
    }
    for (String e : edges) {
      dot.append(e);
    }
    dot.append("}\n");
    Files.createDirectories(dotPath.getParent());
    Files.writeString(dotPath, dot.toString());
    Process p =
        new ProcessBuilder("dot", "-Tsvg", dotPath.toString(), "-o", svgPath.toString())
            .redirectErrorStream(true)
            .start();
    if (p.waitFor() != 0) {
      throw new IllegalStateException("dot failed");
    }
  }

  private static String roleFor(int idx, int size, String verdict, String reason) {
    if ("expired_root".equals(reason) && idx == 0) {
      return "expired_root";
    }
    if ("revoked_intermediate".equals(reason) && idx > 0 && idx < size - 1) {
      return "revoked_intermediate";
    }
    if ("path_length".equals(reason) && idx == size - 1) {
      return "rejected";
    }
    if ("aki_mismatch".equals(reason) && idx == size - 1) {
      return "rejected";
    }
    if ("parse_fail".equals(reason)) {
      return "rejected";
    }
    if ("expired_intermediate".equals(reason) && idx > 0 && idx < size - 1) {
      return "revoked_intermediate";
    }
    if ("not_yet_valid".equals(reason) && idx == size - 1) {
      return "rejected";
    }
    if ("accept".equals(verdict)) {
      return "valid_path";
    }
    if (idx == size - 1) {
      return "rejected";
    }
    return "valid_path";
  }

  private static String sanitize(String s) {
    return s.replaceAll("[^A-Za-z0-9_]", "_");
  }
}
