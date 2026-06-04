package trust.util;

import java.nio.file.Path;

public final class Paths {
  private Paths() {}

  public static Path benchMatrix() {
    return Path.of("/app/data/cases/case_matrix.json");
  }
}
