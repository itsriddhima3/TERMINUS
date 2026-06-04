package decoy;

import java.util.List;

/** Synthetic NDJSON line generator for fetch experiments. */
public final class NdjsonStub {
  private NdjsonStub() {}

  public static List<String> op_stub_a(int n) {
    return java.util.stream.IntStream.range(0, n)
        .mapToObj(i -> "{\"device_id\":\"SYN-" + i + "\"}")
        .toList();
  }
}
