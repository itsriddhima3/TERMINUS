package trust.policy;

import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.List;
import java.util.Map;
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
    if (chain.size() > 6) {
      return "path_length";
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

  private static boolean notAfterBefore(CertSlice cert, String evalInstant) {
    try {
      Instant eval = parseInstant(evalInstant);
      return cert.x509().getNotAfter().toInstant().isBefore(eval);
    } catch (Exception e) {
      return false;
    }
  }

  private static Instant parseInstant(String z) {
    if (z.endsWith("Z") && z.length() == 16 && z.indexOf('T') < 0) {
      return DateTimeFormatter.ofPattern("yyyyMMddHHmmss'Z'")
          .withZone(java.time.ZoneOffset.UTC)
          .parse(z, Instant::from);
    }
    return Instant.parse(z);
  }
}
