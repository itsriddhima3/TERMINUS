package decoy

/**
 * Alternate transcript skimmer retained for compatibility experiments.
 * Not used by the shipping audit path.
 */
object PolicyReader {
    fun skim(text: String): Map<String, String> {
        val lastTag = Regex("POLICY_TAG\\s*:\\s*([A-Z]{2}-\\d{4}-\\d{2})")
            .findAll(text)
            .map { it.groupValues[1] }
            .toList()
            .lastOrNull()
            .orEmpty()
        val allow = Regex("ALLOW_REF_PREFIX\\s*:\\s*(.+)")
            .findAll(text)
            .map { it.groupValues[1].trim() }
            .joinToString("|")
        return mapOf("policy_ref" to lastTag, "allow_ref_prefixes" to allow)
    }
}
