package decoy

import java.time.Instant

object TraceMux {
    fun stamp(): String {
        return Instant.ofEpochMilli(0L).toString()
    }
}

