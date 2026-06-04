package trust.parse;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Chain assembly from PEM corpus (bench path). */
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
    Set<String> seen = new HashSet<>();
    while (cursor != null && seen.add(cursor.cn())) {
      chain.add(0, cursor.cn());
      if (cursor.cn().equals(anchorCn)) {
        break;
      }
      cursor = byCn.get(cursor.issuerCn());
    }
    List<CertSlice> remainder = new ArrayList<>();
    for (CertSlice s : slices) {
      if (!chain.contains(s.cn())) {
        remainder.add(s);
      }
    }
    remainder.sort(Comparator.comparing(CertSlice::cn));
    for (CertSlice s : remainder) {
      chain.add(s.cn());
    }
    if (chain.isEmpty() || !chain.contains(anchorCn) || !chain.contains(leafCn)) {
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
      String aki = child.extensionHex("2.5.29.14");
      String parentDn = parent.cn();
      if (aki != null && parentDn != null && !aki.contains(parentDn)) {
        return false;
      }
    }
    return true;
  }

  public static boolean bench_chain_ok(List<String> chain, String anchorCn, String leafCn) {
    return !chain.isEmpty()
        && chain.get(0).equals(anchorCn)
        && chain.get(chain.size() - 1).equals(leafCn);
  }
}
