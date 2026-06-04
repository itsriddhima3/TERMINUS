package customs.util;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class JsonKit {
  private JsonKit() {}

  private static final Pattern STRING = Pattern.compile("\"((?:\\\\.|[^\"\\\\])*)\"");
  private static final Pattern NUMBER = Pattern.compile("-?\\d+(?:\\.\\d+)?");

  public static String escape(String s) {
    return s.replace("\\", "\\\\").replace("\"", "\\\"");
  }

  public static void writeObject(Path path, Map<String, Object> root) throws IOException {
    Files.createDirectories(path.getParent());
    Files.writeString(path, render(root) + "\n");
  }

  @SuppressWarnings("unchecked")
  private static String render(Object v) {
    if (v == null) return "null";
    if (v instanceof Boolean b) return b ? "true" : "false";
    if (v instanceof Number n) {
      if (n.doubleValue() == Math.rint(n.doubleValue())) return String.valueOf(n.longValue());
      return String.valueOf(n.doubleValue());
    }
    if (v instanceof String s) return "\"" + escape(s) + "\"";
    if (v instanceof Map<?, ?> m) {
      StringBuilder sb = new StringBuilder("{");
      boolean first = true;
      for (Map.Entry<?, ?> e : m.entrySet()) {
        if (!first) sb.append(",");
        first = false;
        sb.append("\"").append(escape(String.valueOf(e.getKey()))).append("\":");
        sb.append(render(e.getValue()));
      }
      return sb.append("}").toString();
    }
    if (v instanceof List<?> list) {
      StringBuilder sb = new StringBuilder("[");
      boolean first = true;
      for (Object o : list) {
        if (!first) sb.append(",");
        first = false;
        sb.append(render(o));
      }
      return sb.append("]").toString();
    }
    throw new IllegalArgumentException("unsupported: " + v.getClass());
  }

  public static Map<String, Object> readObject(Path path) throws IOException {
    String raw = Files.readString(path).trim();
    return parseObject(raw);
  }

  private static Map<String, Object> parseObject(String raw) {
    raw = raw.trim();
    if (!raw.startsWith("{") || !raw.endsWith("}")) {
      throw new IllegalArgumentException("expected object");
    }
    Map<String, Object> out = new LinkedHashMap<>();
    String body = raw.substring(1, raw.length() - 1).trim();
    if (body.isEmpty()) return out;
    int i = 0;
    while (i < body.length()) {
      Matcher sm = STRING.matcher(body.substring(i));
      if (!sm.lookingAt()) throw new IllegalArgumentException("key expected");
      String key = unescape(sm.group(1));
      i += sm.end();
      if (i >= body.length() || body.charAt(i) != ':') throw new IllegalArgumentException("colon");
      i++;
      ParseResult pr = parseValue(body, i);
      out.put(key, pr.value);
      i = pr.next;
      if (i < body.length()) {
        if (body.charAt(i) == ',') i++;
        else if (i < body.length()) throw new IllegalArgumentException("comma");
      }
    }
    return out;
  }

  private static String unescape(String s) {
    return s.replace("\\\"", "\"").replace("\\\\", "\\");
  }

  private record ParseResult(Object value, int next) {}

  private static ParseResult parseValue(String body, int start) {
    int i = start;
    while (i < body.length() && Character.isWhitespace(body.charAt(i))) i++;
    if (i >= body.length()) throw new IllegalArgumentException("value");
    char c = body.charAt(i);
    if (c == '"') {
      Matcher sm = STRING.matcher(body.substring(i));
      if (!sm.lookingAt()) throw new IllegalArgumentException("string");
      return new ParseResult(unescape(sm.group(1)), i + sm.end());
    }
    if (c == '{') {
      int depth = 0;
      int j = i;
      for (; j < body.length(); j++) {
        if (body.charAt(j) == '{') depth++;
        else if (body.charAt(j) == '}') {
          depth--;
          if (depth == 0) {
            j++;
            break;
          }
        }
      }
      return new ParseResult(parseObject(body.substring(i, j)), j);
    }
    if (c == '[') {
      int depth = 0;
      int j = i;
      for (; j < body.length(); j++) {
        if (body.charAt(j) == '[') depth++;
        else if (body.charAt(j) == ']') {
          depth--;
          if (depth == 0) {
            j++;
            break;
          }
        }
      }
      return new ParseResult(parseArray(body.substring(i, j)), j);
    }
    Matcher nm = NUMBER.matcher(body.substring(i));
    if (nm.lookingAt()) {
      String num = nm.group();
      Object val = num.contains(".") ? Double.parseDouble(num) : Long.parseLong(num);
      return new ParseResult(val, i + nm.end());
    }
    if (body.startsWith("true", i)) return new ParseResult(true, i + 4);
    if (body.startsWith("false", i)) return new ParseResult(false, i + 5);
    if (body.startsWith("null", i)) return new ParseResult(null, i + 4);
    throw new IllegalArgumentException("token at " + i);
  }

  private static List<Object> parseArray(String raw) {
    raw = raw.trim();
    if (!raw.startsWith("[") || !raw.endsWith("]")) throw new IllegalArgumentException("array");
    String body = raw.substring(1, raw.length() - 1).trim();
    java.util.ArrayList<Object> out = new java.util.ArrayList<>();
    if (body.isEmpty()) return out;
    int i = 0;
    while (i < body.length()) {
      ParseResult pr = parseValue(body, i);
      out.add(pr.value);
      i = pr.next;
      if (i < body.length() && body.charAt(i) == ',') i++;
    }
    return out;
  }
}
