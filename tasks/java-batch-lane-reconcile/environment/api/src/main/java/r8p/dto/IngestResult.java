package r8p.dto;

public class IngestResult {
  private int accepted;
  private int activeSlots;
  private long rollupQty;

  public IngestResult(int accepted, int activeSlots, long rollupQty) {
    this.accepted = accepted;
    this.activeSlots = activeSlots;
    this.rollupQty = rollupQty;
  }

  public int getAccepted() { return accepted; }
  public int getActiveSlots() { return activeSlots; }
  public long getRollupQty() { return rollupQty; }
}
