package meter;

import meter.app.FetchCmd;
import meter.app.NormalizeCmd;
import meter.app.ReconcileCmd;

public final class Main {
  private Main() {}

  public static void main(String[] args) throws Exception {
    if (args.length < 2) {
      System.err.println("usage: meterctl <fetch|normalize|reconcile> <meter-id>");
      System.exit(2);
    }
    String verb = args[0];
    String meterId = args[1];
    switch (verb) {
      case "fetch" -> FetchCmd.run(meterId);
      case "normalize" -> NormalizeCmd.run(meterId);
      case "reconcile" -> ReconcileCmd.run(meterId);
      default -> {
        System.err.println("unknown verb: " + verb);
        System.exit(2);
      }
    }
  }
}
