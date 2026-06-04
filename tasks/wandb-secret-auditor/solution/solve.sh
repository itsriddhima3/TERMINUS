#!/bin/bash
set -euo pipefail

cat > /app/cli/src/main/kotlin/app/Cli.kt <<'TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_APP_CLI_KT'
package app

import iota.Chk9
import theta.Phase7
import util.Canon
import util.Bytes
import util.Json
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.util.stream.Collectors
import zeta.Gate1

object Cli {
    fun run(runsDir: Path, transcriptDir: Path, out: Path) {
        val transcriptText = Canon.readTranscriptDir(transcriptDir)
        val policy = Gate1.gate_1(transcriptText, emptyList(), emptyMap())

        val runDirs = Files.list(runsDir).filter { Files.isDirectory(it) }.collect(Collectors.toList())
        val runPairs = runDirs.map { rd ->
            val meta = rd.resolve("meta.json")
            val id = if (Files.exists(meta)) {
                (Json.parseObject(Files.readString(meta))["id"] ?: rd.fileName.toString()).toString()
            } else {
                rd.fileName.toString()
            }
            id to rd
        }.sortedBy { it.first }

        val runsOut = mutableListOf<Map<String, Any?>>()
        var totalAlerts = 0
        var invalidApprovals = 0

        for ((id, rd) in runPairs) {
            val findings = Phase7.phase_7(rd, policy)

            @Suppress("UNCHECKED_CAST")
            val alerts = findings.filter { it["kind"] == "alert" } as List<Map<String, Any?>>
            val links = findings.filter { it["kind"] == "link" }
            val artifacts = findings.filter { it["kind"] == "artifact" }

            val approvals = loadApprovals(rd).map { Chk9.chk_9(it, policy) }

            val alertsOut = alerts
                .map { mapOf("code" to it["code"], "path" to it["path"], "snippet" to it["snippet"]) }
                .sortedWith(
                    compareBy(
                        { it["path"].toString() },
                        { it["code"].toString() },
                        { it["snippet"].toString() }
                    )
                )

            val linksOut = links
                .map { mapOf("ref" to it["ref"], "ok" to it["ok"]) }
                .sortedBy { it["ref"].toString() }

            val artifactsOut = artifacts
                .map { mapOf("name" to it["name"], "hash_hex" to it["hash_hex"], "bytes" to it["bytes"]) }
                .sortedBy { it["name"].toString() }

            val approvalsOut = approvals
                .map { mapOf("id" to it["id"], "ok" to it["ok"], "reason" to it["reason"]) }
                .sortedBy { it["id"].toString() }

            totalAlerts += alertsOut.size
            invalidApprovals += approvalsOut.count { (it["ok"] as Boolean) == false }

            runsOut.add(
                linkedMapOf(
                    "id" to id,
                    "alerts" to alertsOut,
                    "approvals" to approvalsOut,
                    "artifacts" to artifactsOut,
                    "links" to linksOut
                )
            )
        }

        val transcriptHash = Canon.transcriptHash(transcriptDir)
        val report = Report.canonical(
            linkedMapOf(
                "policy_ref" to (policy["policy_ref"] ?: ""),
                "transcript_hash" to transcriptHash,
                "runs" to runsOut,
                "totals" to linkedMapOf(
                    "run_count" to runsOut.size,
                    "alert_count" to totalAlerts,
                    "invalid_approval_count" to invalidApprovals
                )
            )
        )
        Json.write(out, report)
    }

    private fun loadApprovals(runDir: Path): List<Map<String, Any?>> {
        val d = runDir.resolve("approvals")
        if (!Files.exists(d)) return emptyList()
        val out = mutableListOf<Map<String, Any?>>()
        val files = Files.list(d).filter { it.fileName.toString().endsWith(".json") }.collect(Collectors.toList())
        files.sortBy { it.fileName.toString() }
        for (p in files) {
            val any = Json.parse(Files.readString(p))
            when (any) {
                is List<*> -> out.addAll(any.map { it as Map<String, Any?> })
                is Map<*, *> -> out.add(any as Map<String, Any?>)
                else -> {}
            }
        }
        return out
    }
}
TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_APP_CLI_KT

cat > /app/core/src/main/kotlin/util/Canon.kt <<'TB3_FILE__APP_CORE_SRC_MAIN_KOTLIN_UTIL_CANON_KT'
package util

import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.util.stream.Collectors

object Canon {
    fun readTranscriptDir(dir: Path): String {
        val files = Files.list(dir).filter { it.fileName.toString().endsWith(".txt") }.collect(Collectors.toList())
        files.sortBy { it.fileName.toString() }
        val sb = StringBuilder()
        for ((idx, p) in files.withIndex()) {
            if (idx != 0) sb.append("\n")
            sb.append(Files.readString(p))
        }
        return sb.toString()
    }

    fun transcriptHash(dir: Path): String {
        val files = Files.list(dir).filter { it.fileName.toString().endsWith(".txt") }.collect(Collectors.toList())
        files.sortBy { it.fileName.toString() }
        val h = java.security.MessageDigest.getInstance("SHA-256")
        for ((idx, p) in files.withIndex()) {
            if (idx != 0) h.update("\n".toByteArray(StandardCharsets.UTF_8))
            h.update(Files.readAllBytes(p))
        }
        val out = h.digest()
        val sb = StringBuilder(out.size * 2)
        for (b in out) sb.append(String.format("%02x", b))
        return sb.toString()
    }
}
TB3_FILE__APP_CORE_SRC_MAIN_KOTLIN_UTIL_CANON_KT

cat > /app/cli/src/main/kotlin/zeta/Gate1.kt <<'TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_ZETA_GATE1_KT'
package zeta

/**
 * Extract an effective policy map from the transcript.
 * Symbol name and signature are committed by the authoring spec.
 */
object Gate1 {
    fun gate_1(a0: String, a1: List<String>, a2: Map<String, String>): Map<String, String> {
    val lines = a0.split("\n")

    var currentTag: String? = null
    var activeTag: String? = null
    val blocks = linkedMapOf<String, MutableList<String>>()

    fun ensure(tag: String) {
        blocks.putIfAbsent(tag, mutableListOf())
    }

    for (ln in lines) {
        val mTag = Regex("POLICY_TAG\\s*:\\s*([A-Z]{2}-\\d{4}-\\d{2})").find(ln)
        if (mTag != null) {
            currentTag = mTag.groupValues[1]
            ensure(currentTag!!)
            continue
        }
        if (currentTag != null) {
            blocks[currentTag!!]!!.add(ln)
        }
        if (Regex("\\bSTATUS\\s*:\\s*ACTIVE\\b").containsMatchIn(ln)) {
            if (currentTag != null) activeTag = currentTag
        }
    }

    val tag = activeTag ?: blocks.keys.lastOrNull().orEmpty()
    val blk = blocks[tag] ?: mutableListOf()
    val activeIdx = blk.indexOfFirst { Regex("\\bSTATUS\\s*:\\s*ACTIVE\\b").containsMatchIn(it) }
    val policyLines = if (activeIdx >= 0) blk.drop(activeIdx + 1) else blk

    val redactions = policyLines.mapNotNull { Regex("^\\s*REDACT\\s*:\\s*(.+)\\s*$").find(it)?.groupValues?.get(1) }.map { it.trim() }
    val allowPrefixes = policyLines.mapNotNull { Regex("^\\s*ALLOW_REF_PREFIX\\s*:\\s*(.+)\\s*$").find(it)?.groupValues?.get(1) }.map { it.trim() }
    val nonceFmt = policyLines.mapNotNull { Regex("^\\s*NONCE_FMT\\s*:\\s*(.+)\\s*$").find(it)?.groupValues?.get(1) }.map { it.trim() }.lastOrNull().orEmpty()
    val keySeed = policyLines.mapNotNull { Regex("^\\s*APPROVAL_KEY\\s*:\\s*(.+)\\s*$").find(it)?.groupValues?.get(1) }.map { it.trim() }.lastOrNull().orEmpty()
    val bindOrder = policyLines.mapNotNull { Regex("^\\s*-\\s*order\\s*:\\s*(.+)\\s*$").find(it)?.groupValues?.get(1) }.map { it.trim() }.lastOrNull().orEmpty()

    return linkedMapOf(
        "policy_ref" to tag,
        "redactions" to redactions.joinToString("|"),
        "allow_ref_prefixes" to allowPrefixes.joinToString("|"),
        "nonce_fmt" to nonceFmt,
        "approval_key" to keySeed,
        "bind_order" to bindOrder
    )
    }
}
TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_ZETA_GATE1_KT

cat > /app/cli/src/main/kotlin/theta/Phase7.kt <<'TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_THETA_PHASE7_KT'
package theta

import util.Bytes
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
            val rel = Paths.normRel(p, runDir)
            val lines = Files.readAllLines(p)
            for (ln in lines) {
                if (ln.contains("api_key=") || ln.contains("token:")) {
                    val snip = redactSnippet(ln.trim().take(180), redactions)
                    out.add(mapOf("kind" to "alert", "code" to "EXPOSED", "path" to rel, "snippet" to snip))
                }
            }
        }
    }

    val refFile = runDir.resolve("links").resolve("refs.txt")
    if (Files.exists(refFile)) {
        val refs = Files.readAllLines(refFile).map { it.trim() }.filter { it.isNotEmpty() }.sorted()
        for (r in refs) {
            val ok = isAllowedRef(r, runDir, allowPrefixes)
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

    return out
    }
}

private fun isAllowedRef(ref: String, runDir: Path, allowPrefixes: List<String>): Boolean {
    if (allowPrefixes.any { ref.startsWith(it) }) {
        if (ref.startsWith("file:")) {
            val raw = ref.removePrefix("file:")
            if (!raw.startsWith("./")) return false
            val resolved = runDir.resolve(raw).normalize().toAbsolutePath()
            val root = runDir.toAbsolutePath().normalize()
            return resolved.startsWith(root)
        }
        return true
    }
    if (!ref.startsWith("file:")) return false
    val raw = ref.removePrefix("file:")
    if (!raw.startsWith("./")) return false
    val resolved = runDir.resolve(raw).normalize().toAbsolutePath()
    val root = runDir.toAbsolutePath().normalize()
    return resolved.startsWith(root)
}

private fun redactSnippet(s: String, rules: List<Regex>): String {
    var out = s
    for (r in rules) {
        out = r.replace(out) { m ->
            val v = m.value
            when {
                v.startsWith("api_key=") -> "api_key=<redacted>"
                v.startsWith("token:") -> "token: <redacted>"
                v.contains("api_key=") -> "api_key=<redacted>"
                v.contains("token:") -> "token: <redacted>"
                else -> "<redacted>"
            }
        }
    }
    return out
}
TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_THETA_PHASE7_KT

cat > /app/cli/src/main/kotlin/iota/Chk9.kt <<'TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_IOTA_CHK9_KT'
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

    val nonceFmt = policy["nonce_fmt"] ?: ""
    val nonceOk = checkNonce(nonceFmt, runId, nonce)

    val key = (policy["approval_key"] ?: "").toByteArray(StandardCharsets.UTF_8)
    val msg = "$scope|$runId|$nonce".toByteArray(StandardCharsets.UTF_8)
    val expect = Bytes.hmacSha256Hex(key, msg)
    val proofOk = proof == expect

    val ok = nonceOk && proofOk
    val reason = when {
        ok -> "ok"
        !nonceOk -> "invalid-nonce"
        else -> "invalid-proof"
    }

    return linkedMapOf(
        "id" to id,
        "ok" to ok,
        "reason" to reason
    )
    }

    private fun checkNonce(fmt: String, runId: String, nonce: String): Boolean {
    // supports "NNC-v2:<run>:<8hex>" style
    val m = Regex("^(NNC-v\\d+):<run>:(<8hex>)$").find(fmt.trim())
    if (m == null) return true
    val prefix = m.groupValues[1]
    val fullPrefix = "$prefix:$runId:"
    if (!nonce.startsWith(fullPrefix)) return false
    val tail = nonce.removePrefix(fullPrefix)
    return Regex("^[0-9a-fA-F]{8}$").matches(tail)
    }
}
TB3_FILE__APP_CLI_SRC_MAIN_KOTLIN_IOTA_CHK9_KT

bash /app/scripts/build-cli.sh