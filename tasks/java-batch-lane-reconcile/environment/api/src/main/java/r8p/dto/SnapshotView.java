package r8p.dto;

public class SnapshotView {
  private String label;
  private long lineCount;
  private long rollupQty;
  private int activeSlots;

  public SnapshotView(String label, long lineCount, long rollupQty, int activeSlots) {
    this.label = label;
    this.lineCount = lineCount;
    this.rollupQty = rollupQty;
    this.activeSlots = activeSlots;
  }

  public String getLabel() { return label; }
  public long getLineCount() { return lineCount; }
  public long getRollupQty() { return rollupQty; }
  public int getActiveSlots() { return activeSlots; }
}
