package trust;

import trust.app.CorpusCmd;
import trust.app.GraphCmd;
import trust.app.PolicyCmd;

public final class Main {
  private Main() {}

  public static void main(String[] args) throws Exception {
    if (args.length < 1) {
      System.err.println("usage: trustaudit <corpus|policy|graph> ...");
      System.exit(2);
    }
    switch (args[0]) {
      case "corpus" -> CorpusCmd.run(args);
      case "policy" -> PolicyCmd.run(args);
      case "graph" -> GraphCmd.run(args);
      default -> {
        System.err.println("unknown verb: " + args[0]);
        System.exit(2);
      }
    }
  }
}
