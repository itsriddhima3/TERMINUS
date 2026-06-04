<?php
declare(strict_types=1);

namespace OverlayInspect\Cli;

use PDO;
use OverlayInspect\Game\PackLoader;
use OverlayInspect\Game\Lifecycle;
use OverlayInspect\Game\Overlap;
use OverlayInspect\Game\Throttle;
use OverlayInspect\Game\Reckon;
use OverlayInspect\Imaging\MagickRunner;
use OverlayInspect\Imaging\AsciiTransformer;
use OverlayInspect\Imaging\Pipeline\Stretch;
use OverlayInspect\Persistence\Tally;
use OverlayInspect\Persistence\Sink;
use OverlayInspect\Persistence\Audit;

/**
 * Main play orchestrator.
 *
 * Reads commands one per line from STDIN, dispatches to subsystems, and
 * persists results. When SCRIPTED_CLOCK=1 is set in the environment the
 * clock advances only via explicit `tick` commands; otherwise the clock
 * tracks wall time read from microtime().
 */
final class Loop {
    private CommandParser $parser;

    public function __construct(
        private readonly PDO $pdo,
        private readonly PackLoader $packLoader,
        private readonly Lifecycle $lifecycle,
        private readonly Stretch $stretch,
        private readonly MagickRunner $magick,
        private readonly AsciiTransformer $ascii,
        private readonly Overlap $overlap,
        private readonly Throttle $throttle,
        private readonly Reckon $reckon,
        private readonly Tally $tally,
        private readonly Sink $sink,
        private readonly Audit $audit,
        private readonly OutputRenderer $renderer,
        private readonly array $gridConfig,
        private readonly array $scoringConfig,
    ) {
        $this->parser = new CommandParser();
    }

    public function play(array $args): int {
        $challengeId = (string)($args[0] ?? '');
        $resumeRowId = isset($args[1]) ? (int)$args[1] : 0;
        if ($challengeId === '') {
            fwrite(STDERR, "play requires a challenge id\n");
            return 2;
        }

        $scripted = getenv('SCRIPTED_CLOCK') === '1';
        $stepMs = $scripted ? 0 : 1;

        if ($resumeRowId > 0) {
            $state = $this->lifecycle->restoreFor($resumeRowId);
            if ($state['challenge_id'] !== $challengeId) {
                fwrite(STDERR, "resume challenge mismatch: db={$state['challenge_id']} requested={$challengeId}\n");
                return 2;
            }
            $clockNow = $state['closed_at_ms'] > 0 ? $state['closed_at_ms'] : $state['opened_at_ms'];
        } else {
            $state = $this->lifecycle->freshFor($challengeId);
            $clockNow = $state['opened_at_ms'];
        }

        $challenge = $this->packLoader->loadChallenge($challengeId);
        $sourceImage = $this->magick->fetch($challenge['scene_a_abs_path']);
        $rendered = $this->stretch->apply(
            $sourceImage,
            (int)$this->gridConfig['target_columns'],
            (int)$this->gridConfig['target_rows'],
        );
        $context = [
            'source_w' => $sourceImage['source_width'],
            'source_h' => $sourceImage['source_height'],
            'fitted_w' => $rendered['fitted_w'],
            'fitted_h' => $rendered['fitted_h'],
        ];

        $closedReason = 'quit';
        $bucketWidth = (int)$this->scoringConfig['throttle_bucket_width_ms'];
        $freeQuota = (int)$this->scoringConfig['throttle_free_quota'];
        $penaltyPerHint = (int)$this->scoringConfig['penalty_per_hint'];

        while (($line = fgets(STDIN)) !== false) {
            if (!$scripted) {
                $clockNow = (int)floor(microtime(true) * 1000);
            } else {
                $clockNow += $stepMs;
            }
            $parsed = $this->parser->parse($line);
            switch ($parsed['cmd']) {
                case 'noop':
                    break;
                case 'tick':
                    $delta = (int)($parsed['args'][0] ?? 0);
                    $clockNow += $delta;
                    break;
                case 'look':
                case 'show':
                    $lines = $this->ascii->transform(
                        $rendered['cells'],
                        $rendered['fitted_w'],
                        $rendered['fitted_h'],
                    );
                    $this->renderer->renderScene($lines);
                    break;
                case 'mark':
                    $col = (int)($parsed['args'][0] ?? 0);
                    $row = (int)($parsed['args'][1] ?? 0);
                    $result = $this->overlap->classify($col, $row, $challenge['polygons'], $context);
                    $seq = $this->tally->snapshot($state['session_row_id'], 'mark') + 1;
                    $this->tally->note($state['session_row_id'], 'mark', [
                        'seq' => $seq,
                        'raised_at_ms' => $clockNow,
                        'input_col' => $col,
                        'input_row' => $row,
                        'matched_region_id' => $result['region_id'],
                        'matched' => $result['matched'] ? 1 : 0,
                    ]);
                    $state['mark_count'] += 1;
                    $this->renderer->renderMark($col, $row, $result);
                    break;
                case 'hint':
                    if (($clockNow - $state['bucket_start_ms']) >= $bucketWidth) {
                        $state['bucket_start_ms'] = $clockNow;
                        $state['bucket_count'] = 0;
                    }
                    $free = $this->throttle->admit(
                        $clockNow,
                        $state['bucket_start_ms'],
                        $state['bucket_count'],
                        $bucketWidth,
                        $freeQuota,
                    );
                    $penalty = $free ? 0 : $penaltyPerHint;
                    $seq = $this->tally->snapshot($state['session_row_id'], 'hint') + 1;
                    $this->tally->note($state['session_row_id'], 'hint', [
                        'seq' => $seq,
                        'raised_at_ms' => $clockNow,
                        'incurred_penalty' => $penalty,
                        'bucket_start_ms' => $state['bucket_start_ms'],
                    ]);
                    $state['hint_count'] += 1;
                    $state['bucket_count'] += 1;
                    $state['last_hint_at_ms'] = $clockNow;
                    $this->renderer->renderHint($penalty);
                    break;
                case 'pause':
                    $closedReason = 'paused';
                    break 2;
                case 'quit':
                    $closedReason = 'quit';
                    break 2;
                case 'unknown':
                    fwrite(STDERR, "unknown command\n");
                    break;
            }
        }

        $this->finalize($state, $challenge, $clockNow, $closedReason);
        return 0;
    }

    private function finalize(array $state, array $challenge, int $clockNow, string $closedReason): void {
        $sessionRowId = (int)$state['session_row_id'];
        $base = (int)$challenge['base_units'];
        $elapsedMs = max(0, $clockNow - (int)$state['opened_at_ms']);
        $elapsedSec = (int)floor($elapsedMs / 1000);
        $sumPenStmt = $this->pdo->prepare(
            'SELECT COALESCE(SUM(incurred_penalty), 0) AS s FROM hints WHERE session_row_id = ?'
        );
        $sumPenStmt->execute([$sessionRowId]);
        $discretePenalties = (int)$sumPenStmt->fetch()['s'];
        $matchStmt = $this->pdo->prepare(
            'SELECT COUNT(*) AS c FROM marks WHERE session_row_id = ? AND matched = 1'
        );
        $matchStmt->execute([$sessionRowId]);
        $matchedMarks = (int)$matchStmt->fetch()['c'];
        $hintStmt = $this->pdo->prepare(
            'SELECT COUNT(*) AS c FROM hints WHERE session_row_id = ?'
        );
        $hintStmt->execute([$sessionRowId]);
        $hintCount = (int)$hintStmt->fetch()['c'];

        $bonusUnits = $matchedMarks * (int)$this->scoringConfig['bonus_per_match']
            + $hintCount * (int)$this->scoringConfig['hint_reveal_bonus'];

        $final = $this->reckon->compose($base, $discretePenalties, $bonusUnits, $elapsedSec);

        $this->pdo->prepare(
            'UPDATE sessions SET closed_at_ms = ?, closed_reason = ? WHERE session_row_id = ?'
        )->execute([$clockNow, $closedReason, $sessionRowId]);

        $components = [
            'base_units' => $base,
            'elapsed_seconds' => $elapsedSec,
            'decay' => $elapsedSec * (int)$this->scoringConfig['decay_per_second'],
            'discrete_penalties' => $discretePenalties,
            'bonus_units' => $bonusUnits,
            'matched_marks' => $matchedMarks,
            'hint_count' => $hintCount,
            'closed_reason' => $closedReason,
        ];
        $this->sink->commit($sessionRowId, $final, $components);
        $this->renderer->renderSummary($sessionRowId, $final, $components);
    }

    public function listPacks(): int {
        $rows = $this->packLoader->listChallenges();
        $this->renderer->renderChallengeList($rows);
        return 0;
    }

    public function describe(string $challengeId): int {
        try {
            $ch = $this->packLoader->loadChallenge($challengeId);
        } catch (\Throwable $e) {
            fwrite(STDERR, $e->getMessage() . "\n");
            return 2;
        }
        fwrite(STDOUT, sprintf(
            "challenge=%s pack=%s source=%dx%d base=%d polygons=%d\n",
            $ch['challenge_id'], $ch['pack_id'],
            $ch['source_width'], $ch['source_height'],
            $ch['base_units'], count($ch['polygons']),
        ));
        return 0;
    }

    public function overlayHelp(): int {
        $this->renderer->renderHelp();
        return 0;
    }

    public function resetDb(): int {
        $this->pdo->exec('DELETE FROM marks');
        $this->pdo->exec('DELETE FROM hints');
        $this->pdo->exec('DELETE FROM sessions');
        $this->pdo->exec('DELETE FROM audit_log');
        $this->audit->record('reset', 'tables emptied');
        return 0;
    }
}
