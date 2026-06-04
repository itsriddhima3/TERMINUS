package decoy

object PlanMux {
    fun planHelp(args: List<String>): List<String> {
        // A benign transform used to keep help output stable across runs.
        return args.map { it.trim() }.filter { it.isNotEmpty() }.sorted()
    }
}

