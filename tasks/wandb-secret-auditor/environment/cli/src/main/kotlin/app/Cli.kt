package app

import iota.Chk9
import theta.Phase7
import util.Canon
import util.Bytes
import util.Json
import java.nio.file.Files
import java.nio.file.Path
import java.util.stream.Collectors
import zeta.Gate1

object Cli {
    fun run(runsDir: Path, transcriptDir: Path, out: Path) {
        val transcript = Canon.readTranscriptDir(transcriptDir)
        val policy = Gate1.gate_1(transcript, listOf("run_alpha", "run_bravo", "run_charlie"), mapOf())

        val runDirs = Files.list(runsDir).filter { Files.isDirectory(it) }.collect(Collectors.toList())
        runDirs.sortByDescending { it.fileName.toString() }
        val runsOut = mutableListOf<Map<String, Any?>>()
        var totalAlerts = 0
        var invalidApprovals = 0

        for (rd in runDirs) {
            val perRun = Phase7.phase_7(rd, policy)
            val approvals = loadApprovals(rd, policy).map { Chk9.chk_9(it, policy) }
            invalidApprovals += approvals.count { (it["ok"] as Boolean) == false }
            @Suppress("UNCHECKED_CAST")
            val alerts = perRun.filter { it["kind"] == "alert" } as List<Map<String, Any?>>
            totalAlerts += alerts.size
            val links = perRun.filter { it["kind"] == "link" }
            val artifacts = perRun.filter { it["kind"] == "artifact" }
            val id = (Json.parseObject(Files.readString(rd.resolve("meta.json")))["id"] ?: rd.fileName.toString()).toString()

            val runObj = linkedMapOf<String, Any?>(
                "id" to id,
                "alerts" to alerts.map { mapOf("code" to it["code"], "path" to it["path"], "snippet" to it["snippet"]) },
                "approvals" to approvals.map { mapOf("id" to it["id"], "ok" to it["ok"], "reason" to it["reason"]) },
                "artifacts" to artifacts.map { mapOf("name" to it["name"], "hash_hex" to it["hash_hex"], "bytes" to it["bytes"]) },
                "links" to links.map { mapOf("ref" to it["ref"], "ok" to it["ok"]) }
            )
            runsOut.add(runObj)
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

    private fun loadApprovals(runDir: Path, policy: Map<String, String>): List<Map<String, Any?>> {
        val d = runDir.resolve("approvals")
        if (!Files.exists(d)) return emptyList()
        val out = mutableListOf<Map<String, Any?>>()
        val files = Files.list(d).filter { it.fileName.toString().endsWith(".json") }.collect(Collectors.toList())
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

