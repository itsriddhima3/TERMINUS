package app

object Report {
    fun canonical(any: Any?): Any? {
        return when (any) {
            is Map<*, *> -> any.entries.sortedBy { it.key.toString() }.associate { (k, v) ->
                k.toString() to canonical(v)
            }
            is List<*> -> any.map { canonical(it) }
            else -> any
        }
    }
}

