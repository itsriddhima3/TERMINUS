package trust.graph.emit;

import java.util.Map;

public final class StyleLedger {
  private StyleLedger() {}

  public static Map<String, String> attrsFor(String role) {
    return switch (role) {
      case "valid_path" -> Map.of("fillcolor", "#e8f5e9", "color", "forestgreen");
      case "rejected" -> Map.of("fillcolor", "orange", "style", "filled");
      case "expired_root" -> Map.of("fillcolor", "gray", "style", "dashed");
      case "revoked_intermediate" -> Map.of("color", "red", "penwidth", "2", "peripheries", "2");
      default -> Map.of();
    };
  }
}
