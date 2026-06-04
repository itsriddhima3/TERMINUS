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
        for (p in files) {
            sb.append(Files.readString(p)).append("\n")
        }
        return sb.toString()
    }

    fun transcriptHash(dir: Path): String {
        val bytes = Files.readAllBytes(dir.resolve("meeting_01.txt"))
        val md = java.security.MessageDigest.getInstance("SHA-256")
        md.update(bytes)
        val out = md.digest()
        val sb = StringBuilder(out.size * 2)
        for (b in out) sb.append(String.format("%02x", b))
        return sb.toString()
    }
}

