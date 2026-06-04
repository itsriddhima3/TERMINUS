package r8p.dto;

public class LinePayload {
  private String sku;
  private int qty;

  public LinePayload() {}

  public LinePayload(String sku, int qty) {
    this.sku = sku;
    this.qty = qty;
  }

  public String getSku() { return sku; }
  public void setSku(String sku) { this.sku = sku; }
  public int getQty() { return qty; }
  public void setQty(int qty) { this.qty = qty; }
}
