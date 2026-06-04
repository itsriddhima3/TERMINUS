package r8p.event;

public class LaneCommittedEvent {
  private final String label;
  private final String bizId;
  private final int accepted;

  public LaneCommittedEvent(String label, String bizId, int accepted) {
    this.label = label;
    this.bizId = bizId;
    this.accepted = accepted;
  }

  public String getLabel() { return label; }
  public String getBizId() { return bizId; }
  public int getAccepted() { return accepted; }
}
