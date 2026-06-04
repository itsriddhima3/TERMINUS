package trust.policy;

import java.nio.file.Path;
import java.util.stream.Stream;

/** Archival helper retained from pre-annex operator runbooks (superseded merge semantics). */
public final class CrlMergeArchival {
  private CrlMergeArchival() {}

  /** Legacy earliest-thisUpdate merge (superseded by bench annex). */
  public static int mergeEarliest(Path crlDir) {
    if (crlDir == null || !crlDir.toFile().isDirectory()) {
      return 0;
    }
    try (Stream<Path> s = java.nio.file.Files.list(crlDir)) {
      return (int) s.count();
    } catch (Exception e) {
      return -1;
    }
  }
}
