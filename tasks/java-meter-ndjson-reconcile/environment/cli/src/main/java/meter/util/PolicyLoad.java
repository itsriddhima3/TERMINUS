package meter.util;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class PolicyLoad {
  private PolicyLoad() {}

  private static final Path POLICY = Path.of("/app/config/bench_policy.toml");

  public static int gapToleranceMin() throws IOException {
    return (int) readDouble("gap_tolerance_min", 15.0);
  }

  public static double deltaToleranceKwh() throws IOException {
    return readDouble("delta_tolerance_kwh", 0.001);
  }

  private static double readDouble(String key, double fallback) throws IOException {
    String body = Files.readString(POLICY);
    Matcher m =
        Pattern.compile("(?m)^" + Pattern.quote(key) + "\\s*=\\s*([0-9.]+)\\s*$")
            .matcher(body);
    if (m.find()) {
      return Double.parseDouble(m.group(1));
    }
    return fallback;
  }
}
