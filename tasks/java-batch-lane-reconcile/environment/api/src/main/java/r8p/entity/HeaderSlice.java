package r8p.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;

@Entity
@Table(name = "header_slice")
public class HeaderSlice {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "partition_label", nullable = false)
  private String partitionLabel;

  @Column(name = "external_biz_id", nullable = false)
  private String externalBizId;

  @Column(name = "stamp_version", nullable = false)
  private Long stampVersion = 0L;

  public Long getId() { return id; }
  public String getPartitionLabel() { return partitionLabel; }
  public void setPartitionLabel(String v) { this.partitionLabel = v; }
  public String getExternalBizId() { return externalBizId; }
  public void setExternalBizId(String v) { this.externalBizId = v; }
  public Long getStampVersion() { return stampVersion; }
}
