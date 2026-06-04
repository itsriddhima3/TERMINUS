package decoy;

import java.util.Map;

/** Palette-only DOT attributes (no trust roles). */
public final class DotTheme {
  private DotTheme() {}

  public static Map<String, String> op_q9(String palette) {
    return Map.of("bgcolor", "white", "fontname", "Helvetica");
  }
}
