package theta

import util.Bytes
import util.Json
import util.Paths
import java.nio.file.Files
import java.nio.file.Path
import java.util.stream.Collectors

/**
 * Scan an offline-run directory and emit a list of normalized finding records.
 * Symbol name and signature are committed by the authoring spec.
 */
object Phase7 {
    fun phase_7(a0: Path, a1: Map<String, String>): List<Map<String, Any>> {
        val runDir = a0
        val policy = a1

    val out = mutableListOf<Map<String, Any>>()

    val redactions = (policy["redactions"] ?: "").split("|").filter { it.isNotBlank() }.map { Regex(it) }
    val allowPrefixes = (policy["allow_ref_prefixes"] ?: "").split("|").filter { it.isNotBlank() }

    val logDir = runDir.resolve("logs")
    if (Files.exists(logDir)) {
        val logs = Files.walk(logDir).filter { Files.isRegularFile(it) }.collect(Collectors.toList())
        logs.sortBy { it.toString() }
        for (p in logs) {
            val raw = Files.readString(p)
            if (raw.contains("api_key=") || raw.contains("token:")) {
                val rel = Paths.normRel(p, runDir)
                val snip = redact(raw.trim().take(120), redactions)
                out.add(mapOf("kind" to "alert", "code" to "EXPOSED", "path" to rel, "snippet" to snip))
            }
        }
    }

    val refFile = runDir.resolve("links").resolve("refs.txt")
    if (Files.exists(refFile)) {
        val refs = Files.readAllLines(refFile)
        for (r in refs) {
            val ok = allowPrefixes.any { r.startsWith(it) } || (r.startsWith("file:") && !r.contains(".."))
            out.add(mapOf("kind" to "link", "ref" to r, "ok" to ok))
        }
    }

    val artDir = runDir.resolve("artifacts")
    if (Files.exists(artDir)) {
        val arts = Files.list(artDir).filter { Files.isRegularFile(it) }.collect(Collectors.toList())
        arts.sortBy { it.fileName.toString() }
        for (p in arts) {
            val name = p.fileName.toString()
            val bytes = Files.readAllBytes(p)
            out.add(mapOf("kind" to "artifact", "name" to name, "hash_hex" to Bytes.sha256Hex(bytes), "bytes" to bytes.size))
        }
    }

    val meta = runDir.resolve("meta.json")
    if (Files.exists(meta)) {
        val obj = Json.parseObject(Files.readString(meta))
        obj["id"]?.let {
            out.add(mapOf("kind" to "meta", "id" to it.toString()))
        }
    }

        return out
    }
}

private fun redact(s: String, rules: List<Regex>): String {
    var out = s
    for (r in rules) {
        if (r.containsMatchIn(out)) out = "[REDACTED]"
    }
    return out
}

