package trust.graph.emit;

import java.util.Map;

public final class StyleLedger {
  private StyleLedger() {}

  public static Map<String, String> attrsFor(String role) {
  return switch (role) {
      case "valid_path" -> Map.of("fillcolor", "#ffffff", "color", "black");
      case "rejected" -> Map.of("fillcolor", "#ffffcc", "style", "filled");
      case "expired_root" -> Map.of("fillcolor", "#dddddd", "style", "solid");
      case "revoked_intermediate" -> Map.of("color", "black", "penwidth", "1");
      default -> Map.of();
    };
  }
}
