package r8p.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.Version;

@Entity
@Table(name = "line_slice")
public class LineSlice {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "header_id", nullable = false)
  private HeaderSlice header;

  private String sku;
  private int qty;

  @Version
  @Column(name = "stamp_version")
  private Long stampVersion;

  public Long getId() { return id; }
  public HeaderSlice getHeader() { return header; }
  public void setHeader(HeaderSlice h) { this.header = h; }
  public String getSku() { return sku; }
  public void setSku(String v) { this.sku = v; }
  public int getQty() { return qty; }
  public void setQty(int v) { this.qty = v; }
}
