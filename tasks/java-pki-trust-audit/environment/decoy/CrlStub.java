package decoy;

import java.nio.file.Path;

/** Archives CRL tar bundles without merge semantics. */
public final class CrlStub {
  private CrlStub() {}

  public static int fn_w7(Path dir) {
    return dir == null ? 0 : dir.getNameCount();
  }
}
