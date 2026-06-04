package r8p.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "partition_dim")
public class PartitionDim {
  @Id
  private String label;

  @Column(name = "cap_slots")
  private int capSlots;

  @Column(name = "active_slots")
  private int activeSlots;

  @Column(name = "rollup_qty")
  private long rollupQty;

  public String getLabel() { return label; }
  public int getCapSlots() { return capSlots; }
  public int getActiveSlots() { return activeSlots; }
  public void setActiveSlots(int v) { this.activeSlots = v; }
  public long getRollupQty() { return rollupQty; }
}
