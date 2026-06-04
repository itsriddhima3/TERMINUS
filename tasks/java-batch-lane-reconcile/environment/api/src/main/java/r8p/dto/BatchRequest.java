package r8p.dto;

import java.util.List;

public class BatchRequest {
  private String externalBizId;
  private List<LinePayload> lines;

  public BatchRequest() {}

  public BatchRequest(String externalBizId, List<LinePayload> lines) {
    this.externalBizId = externalBizId;
    this.lines = lines;
  }

  public String getExternalBizId() { return externalBizId; }
  public void setExternalBizId(String v) { this.externalBizId = v; }
  public List<LinePayload> getLines() { return lines; }
  public void setLines(List<LinePayload> v) { this.lines = v; }
}
