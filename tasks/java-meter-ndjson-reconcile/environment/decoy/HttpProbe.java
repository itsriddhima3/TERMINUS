package decoy;

import java.net.HttpURLConnection;
import java.net.URL;

/** Health-only probe; never writes enrichment artifacts. */
public final class HttpProbe {
  private HttpProbe() {}

  public static boolean op_probe_a(int port) throws Exception {
    HttpURLConnection conn =
        (HttpURLConnection) new URL("http://127.0.0.1:" + port + "/actuator/health").openConnection();
    conn.setConnectTimeout(1000);
    conn.setReadTimeout(1000);
    return conn.getResponseCode() == 200;
  }
}
