package app

import java.nio.file.Path
import kotlin.system.exitProcess

object Main {
    @JvmStatic
    fun main(args: Array<String>) {
        if (args.size != 3) {
            System.err.println("usage: wbaudit <runs_dir> <transcript_dir> <out_json>")
            exitProcess(2)
        }
        val runsDir = Path.of(args[0])
        val transcriptDir = Path.of(args[1])
        val out = Path.of(args[2])
        try {
            Cli.run(runsDir, transcriptDir, out)
        } catch (e: Exception) {
            System.err.println("fatal: ${e.message}")
            exitProcess(1)
        }
    }
}

