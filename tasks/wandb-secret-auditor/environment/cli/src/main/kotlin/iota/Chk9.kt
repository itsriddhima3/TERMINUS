package iota

import util.Bytes
import java.nio.charset.StandardCharsets

/**
 * Validate an approval record and return a structured verdict.
 * Symbol name and signature are committed by the authoring spec.
 */
object Chk9 {
    fun chk_9(a0: Map<String, Any?>, a1: Map<String, String>): Map<String, Any?> {
        val rec = a0
        val policy = a1

    val id = (rec["id"] ?: "").toString()
    val nonce = (rec["nonce"] ?: "").toString()
    val proof = (rec["proof"] ?: "").toString()
    val runId = (rec["run_id"] ?: "").toString()
    val scope = (rec["scope"] ?: "").toString()

    val key = (policy["approval_key"] ?: "").toByteArray(StandardCharsets.UTF_8)
    val msg = "$runId|$nonce|$scope".toByteArray(StandardCharsets.UTF_8)
    val expect = Bytes.hmacSha256Hex(key, msg)
    val ok = (proof == expect)

    val reason = if (ok) "ok" else "invalid-proof"
        return linkedMapOf(
            "id" to id,
            "ok" to ok,
            "reason" to reason
        )
    }
}

