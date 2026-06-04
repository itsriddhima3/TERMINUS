<?php
declare(strict_types=1);

namespace OverlayInspect\Cli;

/**
 * Stdout writer for engine events. Pure side-effect class; no logic.
 */
final class OutputRenderer {
    public function renderHelp(): void {
        $msg = <<<TXT
overlay-inspect — diagnostics-mode CLI

Subcommands:
  play <challenge-id> [<resume-session-row-id>]
  list
  describe <challenge-id>
  overlay-help
  reset

See /app/docs/cli_help.md for details.

TXT;
        fwrite(STDOUT, $msg);
    }

    public function renderMark(int $col, int $row, array $result): void {
        $matched = $result['matched'] ? 'HIT' : 'MISS';
        $rid = $result['region_id'] ?? '-';
        fwrite(STDOUT, "MARK({$col},{$row}) -> {$matched} region={$rid}\n");
    }

    public function renderHint(int $penalty): void {
        fwrite(STDOUT, "HINT issued (penalty={$penalty})\n");
    }

    public function renderScene(array $lines): void {
        foreach ($lines as $line) {
            fwrite(STDOUT, $line . "\n");
        }
    }

    public function renderSummary(int $sessionRowId, int $score, array $components): void {
        fwrite(STDOUT, "SESSION {$sessionRowId} CLOSED score={$score}\n");
        fwrite(STDOUT, 'BREAKDOWN ' . json_encode($components) . "\n");
    }

    public function renderChallengeList(array $rows): void {
        foreach ($rows as $row) {
            fwrite(STDOUT, sprintf(
                "%s\t%s\t%dx%d\n",
                $row['challenge_id'],
                $row['pack_id'],
                (int)$row['source_width'],
                (int)$row['source_height'],
            ));
        }
    }
}
