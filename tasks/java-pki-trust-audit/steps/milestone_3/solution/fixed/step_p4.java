package trust.parse;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class step_p4 {
  private step_p4() {}

  public static List<String> fn_p4(
      List<CertSlice> slices, String anchorCn, String leafCn) {
    Map<String, CertSlice> byCn = new HashMap<>();
    for (CertSlice s : slices) {
      byCn.put(s.cn(), s);
    }
    if (!byCn.containsKey(anchorCn) || !byCn.containsKey(leafCn)) {
      return List.of();
    }
    List<String> chain = new ArrayList<>();
    CertSlice cursor = byCn.get(leafCn);
    while (cursor != null) {
      chain.add(0, cursor.cn());
      if (cursor.cn().equals(anchorCn)) {
        break;
      }
      cursor = byCn.get(cursor.issuerCn());
    }
    if (chain.isEmpty() || !chain.get(0).equals(anchorCn) || !chain.get(chain.size() - 1).equals(leafCn)) {
      return List.of();
    }
    return chain;
  }

  public static boolean aki_link_ok(List<CertSlice> slices, List<String> chain) {
    Map<String, CertSlice> byCn = new HashMap<>();
    for (CertSlice s : slices) {
      byCn.put(s.cn(), s);
    }
    for (int i = 1; i < chain.size(); i++) {
      CertSlice child = byCn.get(chain.get(i));
      CertSlice parent = byCn.get(chain.get(i - 1));
      if (child == null || parent == null) {
        return false;
      }
      String aki = child.keyIdHex("2.5.29.35");
      String parentSki = parent.keyIdHex("2.5.29.14");
      if (aki != null && parentSki != null && !aki.equals(parentSki)) {
        return false;
      }
    }
    return true;
  }
}
