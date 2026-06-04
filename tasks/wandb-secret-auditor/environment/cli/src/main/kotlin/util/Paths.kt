package util

import java.nio.file.Path

object Paths {
    fun normRel(p: Path, root: Path): String {
        val abs = p.toAbsolutePath().normalize()
        val r = root.toAbsolutePath().normalize()
        val rel = r.relativize(abs).toString().replace('\\', '/')
        return "/" + rel
    }
}

