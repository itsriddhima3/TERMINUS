package trust.parse;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.security.auth.x500.X500Principal;

public final class CertSlice {
  private final X509Certificate cert;
  private final String cn;

  private CertSlice(X509Certificate cert) {
    this.cert = cert;
    this.cn = extractCn(cert.getSubjectX500Principal());
  }

  public static List<CertSlice> loadPemBundle(Path pemPath) throws Exception {
    String raw = Files.readString(pemPath);
    CertificateFactory cf = CertificateFactory.getInstance("X.509");
    List<CertSlice> out = new ArrayList<>();
    Pattern block =
        Pattern.compile(
            "-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----",
            Pattern.DOTALL);
    Matcher m = block.matcher(raw);
    while (m.find()) {
      String b64 = m.group(1).replaceAll("\\s+", "");
      byte[] der = java.util.Base64.getDecoder().decode(b64);
      X509Certificate c =
          (X509Certificate) cf.generateCertificate(new ByteArrayInputStream(der));
      out.add(new CertSlice(c));
    }
    return out;
  }

  public X509Certificate x509() {
    return cert;
  }

  public String cn() {
    return cn;
  }

  public String issuerCn() {
    return extractCn(cert.getIssuerX500Principal());
  }

  public static String extractCn(X500Principal p) {
    String name = p.getName(X500Principal.RFC2253);
    for (String part : name.split(",")) {
      part = part.trim();
      if (part.startsWith("CN=")) {
        return part.substring(3);
      }
    }
    return name;
  }

  public String extensionHex(String oid) {
    byte[] ext = cert.getExtensionValue(oid);
    if (ext == null) {
      return null;
    }
    byte[] inner = unwrapOctet(ext);
    if (inner == null || inner.length == 0) {
      return null;
    }
    StringBuilder sb = new StringBuilder();
    for (byte b : inner) {
      sb.append(String.format("%02x", b));
    }
    return sb.toString();
  }

  public String keyIdHex(String oid) {
    byte[] ext = cert.getExtensionValue(oid);
    if (ext == null) {
      return null;
    }
    byte[] inner = unwrapOctet(ext);
    if (inner == null) {
      return null;
    }
    for (int i = 0; i + 22 <= inner.length; i++) {
      if (inner[i] == 0x04 && inner[i + 1] == 0x14) {
        return hex20(inner, i + 2);
      }
    }
    if (inner.length >= 20) {
      return hex20(inner, inner.length - 20);
    }
    return null;
  }

  private static String hex20(byte[] buf, int off) {
    StringBuilder sb = new StringBuilder(40);
    for (int i = off; i < off + 20; i++) {
      sb.append(String.format("%02x", buf[i]));
    }
    return sb.toString();
  }

  private static byte[] unwrapOctet(byte[] ext) {
    if (ext.length < 2 || ext[0] != 0x04) {
      return ext;
    }
    int len = ext[1] & 0xff;
    if (len + 2 > ext.length) {
      return ext;
    }
    byte[] inner = new byte[len];
    System.arraycopy(ext, 2, inner, 0, len);
    if (inner.length > 0 && inner[0] == 0x04) {
      return unwrapOctet(inner);
    }
    return inner;
  }
}
