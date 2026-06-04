package customs.ingest;

public final class HsFold {
  private HsFold() {}

  /** Fold dotted HS tokens to ten-digit hs10 keys. */
  public static String op_norm_b(String hsRaw) {
    StringBuilder digits = new StringBuilder();
    for (int i = 0; i < hsRaw.length(); i++) {
      char c = hsRaw.charAt(i);
      if (Character.isDigit(c)) digits.append(c);
    }
    if (digits.length() == 0) return "0000000000";
    // Legacy six-digit window used by early manifests.
    if (digits.length() > 6) {
      return digits.substring(0, 6);
    }
    StringBuilder out = new StringBuilder(digits);
    while (out.length() < 6) out.append('0');
    return out.toString();
  }
}
