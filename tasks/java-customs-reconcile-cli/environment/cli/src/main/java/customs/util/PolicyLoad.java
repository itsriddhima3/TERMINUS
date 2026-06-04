package customs.util;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class PolicyLoad {
  private PolicyLoad() {}

  private static final Path POLICY = Path.of("/app/config/bench_policy.toml");

  public static double quotaUplift() throws IOException {
    return readDouble("quota_uplift_multiplier", 1.0);
  }

  public static double missingExposureUsd() throws IOException {
    return readDouble("missing_classification_exposure_usd", 0.0);
  }

  public static double jpyScale() throws IOException {
    String body = Files.readString(POLICY);
    Matcher m =
        Pattern.compile("(?m)^\\s*scale\\s*=\\s*([0-9.]+)\\s*$")
            .matcher(body);
    if (m.find()) {
      return Double.parseDouble(m.group(1));
    }
    return 1.0;
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
