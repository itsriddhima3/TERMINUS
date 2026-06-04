package decoy;

import java.util.List;

/** Synthetic row generator for ingest experiments. */
public final class CsvStub {
  private CsvStub() {}

  public static List<String> op_stub_a(int n) {
    return java.util.stream.IntStream.range(0, n).mapToObj(i -> "SYN-" + i).toList();
  }
}
