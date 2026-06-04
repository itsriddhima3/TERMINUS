package util

import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path

object Json {
    fun write(path: Path, obj: Any?) {
        val txt = encode(obj) + "\n"
        path.parent?.let { Files.createDirectories(it) }
        Files.write(path, txt.toByteArray(StandardCharsets.UTF_8))
    }

    fun encode(any: Any?): String = MiniJson.encode(any)
    fun parse(txt: String): Any? = MiniJson.parse(txt)
    fun parseObject(txt: String): Map<String, Any?> = parse(txt) as Map<String, Any?>
}

private object MiniJson {
    fun encode(any: Any?): String {
        return when (any) {
            null -> "null"
            is Map<*, *> -> any.entries.sortedBy { it.key.toString() }.joinToString(
                prefix = "{",
                postfix = "}",
                separator = ","
            ) { e ->
                val k = e.key.toString()
                "\"${esc(k)}\":${encode(e.value)}"
            }
            is List<*> -> any.joinToString(prefix = "[", postfix = "]", separator = ",") { encode(it) }
            is String -> "\"${esc(any)}\""
            is Boolean -> if (any) "true" else "false"
            is Int, is Long, is Double, is Float -> any.toString()
            is Number -> any.toString()
            else -> "\"${esc(any.toString())}\""
        }
    }

    fun parse(txt: String): Any? {
        val p = Parser(txt)
        val v = p.parseValue()
        p.skipWs()
        require(p.eof()) { "trailing content" }
        return v
    }

    private fun esc(s: String): String = s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")

    private class Parser(private val s: String) {
        private var i: Int = 0

        fun eof(): Boolean = i >= s.length

        fun skipWs() {
            while (!eof() && s[i].isWhitespace()) i++
        }

        fun parseValue(): Any? {
            skipWs()
            require(!eof()) { "eof" }
            return when (s[i]) {
                '{' -> parseObj()
                '[' -> parseArr()
                '"' -> parseStr()
                't' -> { lit("true"); true }
                'f' -> { lit("false"); false }
                'n' -> { lit("null"); null }
                else -> parseNum()
            }
        }

        private fun parseObj(): Map<String, Any?> {
            eat('{')
            skipWs()
            val out = linkedMapOf<String, Any?>()
            if (peek('}')) { eat('}'); return out }
            while (true) {
                skipWs()
                val k = parseStr()
                skipWs()
                eat(':')
                val v = parseValue()
                out[k] = v
                skipWs()
                if (peek('}')) { eat('}'); break }
                eat(',')
            }
            return out
        }

        private fun parseArr(): List<Any?> {
            eat('[')
            skipWs()
            val out = mutableListOf<Any?>()
            if (peek(']')) { eat(']'); return out }
            while (true) {
                out.add(parseValue())
                skipWs()
                if (peek(']')) { eat(']'); break }
                eat(',')
            }
            return out
        }

        private fun parseStr(): String {
            eat('"')
            val sb = StringBuilder()
            while (true) {
                require(!eof()) { "eof in string" }
                val c = s[i++]
                if (c == '"') break
                if (c == '\\') {
                    require(!eof()) { "eof in escape" }
                    val e = s[i++]
                    sb.append(
                        when (e) {
                            '"', '\\', '/' -> e
                            'n' -> '\n'
                            'r' -> '\r'
                            't' -> '\t'
                            else -> e
                        }
                    )
                } else {
                    sb.append(c)
                }
            }
            return sb.toString()
        }

        private fun parseNum(): Any {
            val start = i
            if (s[i] == '-') i++
            while (!eof() && s[i].isDigit()) i++
            var isFloat = false
            if (!eof() && s[i] == '.') {
                isFloat = true
                i++
                while (!eof() && s[i].isDigit()) i++
            }
            val raw = s.substring(start, i)
            return if (isFloat) raw.toDouble() else raw.toLong()
        }

        private fun lit(w: String) {
            require(s.regionMatches(i, w, 0, w.length)) { "expected $w" }
            i += w.length
        }

        private fun eat(c: Char) {
            require(!eof() && s[i] == c) { "expected '$c'" }
            i++
        }

        private fun peek(c: Char): Boolean = !eof() && s[i] == c
    }
}

