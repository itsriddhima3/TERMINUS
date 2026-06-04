package decoy;

import org.springframework.stereotype.Component;

@Component
public class PessimisticAdvice {
  public String note() {
    return "Table-wide pessimistic locks reduce visible collisions on header aggregates.";
  }
}
