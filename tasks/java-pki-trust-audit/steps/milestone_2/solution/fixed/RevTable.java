package trust.policy;

import java.io.ByteArrayInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.cert.X509CRL;
import java.security.cert.X509CRLEntry;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import trust.parse.CertSlice;

public final class RevTable {
  private final Map<String, Set<String>> revokedByIssuer = new HashMap<>();
  private final Map<String, String> issuerThisUpdate = new HashMap<>();

  public static RevTable empty() {
    return new RevTable();
  }

  public static RevTable mergeGlob(String globPattern) throws Exception {
    RevTable acc = new RevTable();
    Path dir = Path.of(globPattern).getParent();
    String tail = Path.of(globPattern).getFileName().toString().replace("*", ".*");
    Pattern pat = Pattern.compile(tail);
    if (dir == null || !Files.isDirectory(dir)) {
      return acc;
    }
    try (Stream<Path> stream = Files.list(dir)) {
      for (Path p : stream.filter(Files::isRegularFile).sorted().toList()) {
        if (!pat.matcher(p.getFileName().toString()).matches()) {
          continue;
        }
        acc.ingest(p);
      }
    }
    return acc;
  }

  private void ingest(Path crlPath) throws Exception {
    byte[] der = Files.readAllBytes(crlPath);
    X509CRL crl =
        (X509CRL)
            java.security.cert.CertificateFactory.getInstance("X.509")
                .generateCRL(new ByteArrayInputStream(der));
    String issuer = CertSlice.extractCn(crl.getIssuerX500Principal());
    String thisUpdate = generalized(crl.getThisUpdate());
    String prev = issuerThisUpdate.get(issuer);
    if (prev == null || thisUpdate.compareTo(prev) > 0) {
      Set<String> serials = new HashSet<>();
      if (crl.getRevokedCertificates() != null) {
        for (X509CRLEntry e : crl.getRevokedCertificates()) {
          serials.add(e.getSerialNumber().toString(16).toLowerCase());
        }
      }
      revokedByIssuer.put(issuer, serials);
      issuerThisUpdate.put(issuer, thisUpdate);
    }
  }

  public boolean isRevoked(String serialHex) {
    String norm = serialHex.toLowerCase();
    for (Set<String> serials : revokedByIssuer.values()) {
      if (serials.contains(norm)) {
        return true;
      }
    }
    return false;
  }

  private static String generalized(java.util.Date d) {
    return java.time.format.DateTimeFormatter.ofPattern("yyyyMMddHHmmss'Z'")
        .withZone(java.time.ZoneOffset.UTC)
        .format(d.toInstant());
  }
}
