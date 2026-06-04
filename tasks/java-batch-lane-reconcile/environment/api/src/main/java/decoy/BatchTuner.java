package decoy;

import org.springframework.stereotype.Component;

@Component
public class BatchTuner {
  public int reportingFetchSize() {
    return 250;
  }
}
