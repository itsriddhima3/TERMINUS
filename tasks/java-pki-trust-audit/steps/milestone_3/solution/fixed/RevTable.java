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
  private final Set<String> revokedSerials = new HashSet<>();
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
      revokedSerials.clear();
      issuerThisUpdate.put(issuer, thisUpdate);
      if (crl.getRevokedCertificates() != null) {
        for (X509CRLEntry e : crl.getRevokedCertificates()) {
          revokedSerials.add(e.getSerialNumber().toString(16).toLowerCase());
        }
      }
    }
  }

  public boolean isRevoked(String serialHex) {
    return revokedSerials.contains(serialHex.toLowerCase());
  }

  private static String generalized(java.util.Date d) {
    return java.time.format.DateTimeFormatter.ofPattern("yyyyMMddHHmmss'Z'")
        .withZone(java.time.ZoneOffset.UTC)
        .format(d.toInstant());
  }
}
