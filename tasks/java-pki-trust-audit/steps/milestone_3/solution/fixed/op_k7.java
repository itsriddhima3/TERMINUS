package trust.policy;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.TimeZone;
import trust.parse.CertSlice;
import trust.parse.step_p4;

public final class op_k7 {
  private op_k7() {}

  public static String apply(
      Map<String, Object> caseRow,
      List<CertSlice> slices,
      List<String> chain,
      RevTable rev,
      String evalInstant) {
    if (chain.isEmpty()) {
      return "parse_fail";
    }
    Map<String, CertSlice> byCn = new java.util.HashMap<>();
    for (CertSlice s : slices) {
      byCn.put(s.cn(), s);
    }
    CertSlice anchor = byCn.get(chain.get(0));
    if (anchor != null && notAfterBefore(anchor, evalInstant)) {
      return "expired_root";
    }
    if (chain.size() > 4) {
      return "path_length";
    }
    for (int i = 1; i < chain.size() - 1; i++) {
      CertSlice mid = byCn.get(chain.get(i));
      if (mid != null && notAfterBefore(mid, evalInstant)) {
        return "expired_intermediate";
      }
    }
    CertSlice leaf = byCn.get(chain.get(chain.size() - 1));
    if (leaf != null && notBeforeAfter(leaf, evalInstant)) {
      return "not_yet_valid";
    }
    for (CertSlice s : slices) {
      String serial = s.x509().getSerialNumber().toString(16);
      if (rev.isRevoked(serial)) {
        if (!s.cn().equals(chain.get(chain.size() - 1))) {
          return "revoked_intermediate";
        }
      }
    }
    if (!step_p4.aki_link_ok(slices, chain)) {
      return "aki_mismatch";
    }
    return "accept";
  }

  private static Date parseEval(String evalInstant) throws Exception {
    SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMddHHmmss'Z'");
    sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
    return sdf.parse(evalInstant);
  }

  private static boolean notAfterBefore(CertSlice cert, String evalInstant) {
    try {
      return cert.x509().getNotAfter().before(parseEval(evalInstant));
    } catch (Exception e) {
      return false;
    }
  }

  private static boolean notBeforeAfter(CertSlice cert, String evalInstant) {
    try {
      return cert.x509().getNotBefore().after(parseEval(evalInstant));
    } catch (Exception e) {
      return false;
    }
  }
}
