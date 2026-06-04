package trust.util;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Minimal JSON read/write for bench outputs (no external deps). */
public final class JsonKit {
  private JsonKit() {}

  @SuppressWarnings("unchecked")
  public static Map<String, Object> readObject(Path path) throws IOException {
    String raw = Files.readString(path);
    Object v = parseValue(raw.trim());
    if (!(v instanceof Map)) {
      throw new IOException("expected object at " + path);
    }
    return (Map<String, Object>) v;
  }

  public static void writeObject(Path path, Map<String, Object> root) throws IOException {
    Files.createDirectories(path.getParent());
    Files.writeString(path, stringify(root, 0) + "\n");
  }

  private static String stringify(Object v, int indent) {
    if (v == null) {
      return "null";
    }
    if (v instanceof Boolean b) {
      return b ? "true" : "false";
    }
    if (v instanceof Number n) {
      return n.toString();
    }
    if (v instanceof String s) {
      return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }
    if (v instanceof List<?> list) {
      if (list.isEmpty()) {
        return "[]";
      }
      String pad = "  ".repeat(indent + 1);
      StringBuilder sb = new StringBuilder("[\n");
      for (int i = 0; i < list.size(); i++) {
        sb.append(pad).append(stringify(list.get(i), indent + 1));
        if (i + 1 < list.size()) {
          sb.append(",");
        }
        sb.append("\n");
      }
      sb.append("  ".repeat(indent)).append("]");
      return sb.toString();
    }
    if (v instanceof Map<?, ?> map) {
      if (map.isEmpty()) {
        return "{}";
      }
      String pad = "  ".repeat(indent + 1);
      StringBuilder sb = new StringBuilder("{\n");
      int i = 0;
      for (Map.Entry<?, ?> e : map.entrySet()) {
        sb.append(pad)
            .append("\"")
            .append(e.getKey())
            .append("\": ")
            .append(stringify(e.getValue(), indent + 1));
        if (++i < map.size()) {
          sb.append(",");
        }
        sb.append("\n");
      }
      sb.append("  ".repeat(indent)).append("}");
      return sb.toString();
    }
    return "\"" + String.valueOf(v) + "\"";
  }

  private static Object parseValue(String s) {
    if (s.startsWith("{")) {
      return parseObject(s);
    }
    if (s.startsWith("[")) {
      return parseArray(s);
    }
    if (s.equals("true")) {
      return true;
    }
    if (s.equals("false")) {
      return false;
    }
    if (s.equals("null")) {
      return null;
    }
    if (s.startsWith("\"")) {
      return s.substring(1, s.length() - 1);
    }
    if (s.contains(".")) {
      return Double.parseDouble(s);
    }
    return Long.parseLong(s);
  }

  private static Map<String, Object> parseObject(String s) {
    Map<String, Object> out = new LinkedHashMap<>();
    String body = s.substring(1, s.length() - 1).trim();
    if (body.isEmpty()) {
      return out;
    }
    for (String part : splitTop(body)) {
      int colon = part.indexOf(':');
      String key = part.substring(0, colon).trim();
      key = key.substring(1, key.length() - 1);
      String val = part.substring(colon + 1).trim();
      out.put(key, parseValue(val));
    }
    return out;
  }

  private static List<Object> parseArray(String s) {
    String body = s.substring(1, s.length() - 1).trim();
    java.util.ArrayList<Object> out = new java.util.ArrayList<>();
    if (body.isEmpty()) {
      return out;
    }
    for (String part : splitTop(body)) {
      out.add(parseValue(part.trim()));
    }
    return out;
  }

  private static List<String> splitTop(String body) {
    java.util.ArrayList<String> parts = new java.util.ArrayList<>();
    int depth = 0;
    boolean inStr = false;
    int start = 0;
    for (int i = 0; i < body.length(); i++) {
      char c = body.charAt(i);
      if (c == '"' && (i == 0 || body.charAt(i - 1) != '\\')) {
        inStr = !inStr;
      }
      if (!inStr) {
        if (c == '{' || c == '[') {
          depth++;
        } else if (c == '}' || c == ']') {
          depth--;
        } else if (c == ',' && depth == 0) {
          parts.add(body.substring(start, i));
          start = i + 1;
        }
      }
    }
    parts.add(body.substring(start));
    return parts;
  }

  @SuppressWarnings("unchecked")
  public static List<Map<String, Object>> objectList(Map<String, Object> root, String key) {
    Object raw = root.get(key);
    if (!(raw instanceof List<?> list)) {
      throw new IllegalArgumentException("missing list: " + key);
    }
    java.util.ArrayList<Map<String, Object>> out = new java.util.ArrayList<>();
    for (Object o : list) {
      out.add((Map<String, Object>) o);
    }
    return out;
  }

  public static String str(Map<String, Object> m, String key) {
    Object v = m.get(key);
    return v == null ? null : String.valueOf(v);
  }

  public static boolean bool(Map<String, Object> m, String key) {
    Object v = m.get(key);
    return v instanceof Boolean b && b;
  }
}
