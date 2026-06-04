package zeta

/**
 * Extract an effective policy map from the transcript.
 * Symbol name and signature are committed by the authoring spec.
 */
object Gate1 {
    fun gate_1(a0: String, a1: List<String>, a2: Map<String, String>): Map<String, String> {
        val transcript = a0

    val tags = Regex("POLICY_TAG\\s*:\\s*([A-Z]{2}-\\d{4}-\\d{2})")
        .findAll(transcript)
        .map { it.groupValues[1] }
        .toList()
    val policyRef = tags.lastOrNull() ?: ""

    val redactions = Regex("REDACT\\s*:\\s*(.+)").findAll(transcript).map { it.groupValues[1].trim() }.toList()
    val allowPrefixes = Regex("ALLOW_REF_PREFIX\\s*:\\s*(.+)").findAll(transcript).map { it.groupValues[1].trim() }.toList()
    val nonceFmt = Regex("NONCE_FMT\\s*:\\s*(.+)").findAll(transcript).map { it.groupValues[1].trim() }.toList().lastOrNull() ?: ""
    val keySeed = Regex("APPROVAL_KEY\\s*:\\s*(.+)").findAll(transcript).map { it.groupValues[1].trim() }.toList().lastOrNull() ?: ""

        return linkedMapOf(
            "policy_ref" to policyRef,
            "redactions" to redactions.joinToString("|"),
            "allow_ref_prefixes" to allowPrefixes.joinToString("|"),
            "nonce_fmt" to nonceFmt,
            "approval_key" to keySeed
        )
    }
}

