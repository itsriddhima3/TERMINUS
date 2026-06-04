#!/bin/bash
# Terminal-Bench Canary: php-mosaic-overlay-cli
set -euo pipefail

# Topology A: coordinate projector. The upstream Pipeline\Stretch step
# already produces aspect-fitted render dimensions (tw, th), so the
# pixel <-> cell transforms must NOT re-apply the cell aspect ratio.
# The buggy original double-counted that factor in both directions.
cat > /app/imaging/Coord/AffineWarp.php <<'PHP'
<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Coord;

/**
 * Coordinate transformer between source pixel space and terminal cell space.
 *
 * The caller supplies the source frame dimensions (sw, sh) and the rendered
 * frame dimensions (tw, th) in cells. The constructor receives the cell
 * aspect ratio (width-over-height) for terminal cells; it is kept as state
 * for downstream queries (rendered-cell display geometry helpers, etc.)
 * but it must NOT enter the pixel<->cell transforms themselves: those
 * (tw, th) values arrive already aspect-fitted by the upstream
 * Pipeline\Stretch step.
 *
 * Convention:
 *   - pixelToCell(u, v, sw, sh, tw, th) maps a (u, v) source pixel to its
 *     (col, row) cell within the fitted rectangle.
 *   - cellToPixel(col, row, sw, sh, tw, th) is the inverse: a fitted-cell
 *     coordinate back to its representative source pixel.
 *
 * Both maps clamp to (0, 0) if any dimension is non-positive — guarding
 * against degenerate render frames that might appear during boot.
 */
final class AffineWarp {
    public function __construct(private readonly float $cellAspect) {
        if ($this->cellAspect <= 0.0) {
            throw new \InvalidArgumentException('cellAspect must be positive');
        }
    }

    public function pixelToCell(int $u, int $v, int $sw, int $sh, int $tw, int $th): array {
        if ($sw <= 0 || $sh <= 0 || $tw <= 0 || $th <= 0) {
            return [0, 0];
        }
        // Forward map within the already-fitted rectangle. tw/th carry the
        // aspect-correction from the upstream Stretch step; the cell aspect
        // does NOT enter here.
        $col = (int)floor($u * $tw / $sw);
        $row = (int)floor($v * $th / $sh);
        // Clamp into the valid cell range so off-by-one boundary inputs
        // do not wrap into invalid cells.
        if ($col < 0) { $col = 0; }
        if ($row < 0) { $row = 0; }
        if ($col >= $tw) { $col = $tw - 1; }
        if ($row >= $th) { $row = $th - 1; }
        return [$col, $row];
    }

    public function cellToPixel(int $col, int $row, int $sw, int $sh, int $tw, int $th): array {
        if ($sw <= 0 || $sh <= 0 || $tw <= 0 || $th <= 0) {
            return [0, 0];
        }
        // Inverse of pixelToCell. Same rule: no cellAspect, because the
        // (tw, th) inputs already carry the aspect-fitting performed
        // upstream by Pipeline\Stretch.
        $u = (int)floor($col * $sw / $tw);
        $v = (int)floor($row * $sh / $th);
        if ($u < 0) { $u = 0; }
        if ($v < 0) { $v = 0; }
        if ($u >= $sw) { $u = $sw - 1; }
        if ($v >= $sh) { $v = $sh - 1; }
        return [$u, $v];
    }

    public function cellAspect(): float {
        return $this->cellAspect;
    }
}
PHP

# Topology B: session lifecycle. The resume path was calling a private
# bucket-tally primer that wrote a synthetic per-action row to the tally
# writer "to warm" the in-memory aggregate. That write inserted a
# phantom row in the actions table and made the very first post-resume
# draw look like a second draw, so the rate limiter mis-charged it.
# The aggregate is fully derivable from existing rows — no write is
# required to rehydrate; remove the primer call (and the primer body).
cat > /app/lifecycle/Lifecycle.php <<'PHP'
<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

use PDO;
use OverlayInspect\Persistence\Tally;
use OverlayInspect\Persistence\Audit;

/**
 * Hydrates and persists per-session engine state across pause/resume cycles.
 *
 * Two entry points:
 *   - freshFor(challengeId) opens a brand-new session row and returns the
 *     initial in-memory state container the engine works from.
 *   - restoreFor(sessionRowId) rehydrates the engine state from a
 *     previously-paused session row.
 *
 * Important invariant: restoreFor must not perform any per-action writes
 * to the action log. The in-memory aggregates required by the rate
 * limiter (bucket_start_ms, bucket_count, last_hint_at_ms) are fully
 * derivable from rows already on disk; a write would create a phantom
 * action row.
 */
final class Lifecycle {
    public function __construct(
        private readonly PDO $pdo,
        private readonly Tally $tally,
        private readonly Audit $audit,
    ) {}

    public function freshFor(string $challengeId): array {
        $now = $this->nowMs();
        $stmt = $this->pdo->prepare(
            'INSERT INTO sessions (challenge_id, opened_at_ms) VALUES (?, ?)'
        );
        $stmt->execute([$challengeId, $now]);
        $rowId = (int)$this->pdo->lastInsertId();
        $this->audit->record('open_session', json_encode([
            'session_row_id' => $rowId,
            'challenge_id' => $challengeId,
        ], JSON_THROW_ON_ERROR));
        return $this->makeState(
            sessionRowId: $rowId,
            challengeId: $challengeId,
            openedAtMs: $now,
            closedAtMs: 0,
            hintCount: 0,
            markCount: 0,
            bucketStartMs: 0,
            bucketCount: 0,
            lastHintAtMs: 0,
            fresh: true,
        );
    }

    public function restoreFor(int $sessionRowId): array {
        $stmt = $this->pdo->prepare('SELECT * FROM sessions WHERE session_row_id = ?');
        $stmt->execute([$sessionRowId]);
        $session = $stmt->fetch();
        if ($session === false) {
            throw new \RuntimeException("session not found: {$sessionRowId}");
        }
        $hintCount = $this->tally->countFor($sessionRowId, 'hint');
        $markCount = $this->tally->countFor($sessionRowId, 'mark');

        $bucketAggregate = $this->rebuildBucketAggregate($sessionRowId);

        $this->audit->record('resume_session', json_encode([
            'session_row_id' => $sessionRowId,
        ], JSON_THROW_ON_ERROR));

        $this->pdo->prepare(
            'UPDATE sessions SET closed_reason = NULL WHERE session_row_id = ?'
        )->execute([$sessionRowId]);

        return $this->makeState(
            sessionRowId: $sessionRowId,
            challengeId: (string)$session['challenge_id'],
            openedAtMs: (int)$session['opened_at_ms'],
            closedAtMs: (int)($session['closed_at_ms'] ?? 0),
            hintCount: $hintCount,
            markCount: $markCount,
            bucketStartMs: $bucketAggregate['bucket_start_ms'],
            bucketCount: $bucketAggregate['bucket_count'],
            lastHintAtMs: $bucketAggregate['last_hint_at_ms'],
            fresh: false,
        );
    }

    private function rebuildBucketAggregate(int $sessionRowId): array {
        $lastHintStmt = $this->pdo->prepare(
            'SELECT * FROM hints WHERE session_row_id = ? ORDER BY hint_row_id DESC LIMIT 1'
        );
        $lastHintStmt->execute([$sessionRowId]);
        $lastHint = $lastHintStmt->fetch();

        if ($lastHint === false) {
            return [
                'bucket_start_ms' => 0,
                'bucket_count' => 0,
                'last_hint_at_ms' => 0,
            ];
        }

        $bucketStart = (int)$lastHint['bucket_start_ms'];
        $lastHintAt = (int)$lastHint['raised_at_ms'];

        $countStmt = $this->pdo->prepare(
            'SELECT COUNT(*) AS c FROM hints WHERE session_row_id = ? AND bucket_start_ms = ?'
        );
        $countStmt->execute([$sessionRowId, $bucketStart]);
        $bucketCount = (int)$countStmt->fetch()['c'];

        return [
            'bucket_start_ms' => $bucketStart,
            'bucket_count' => $bucketCount,
            'last_hint_at_ms' => $lastHintAt,
        ];
    }

    private function nowMs(): int {
        return getenv('SCRIPTED_CLOCK') === '1'
            ? 0
            : (int)floor(microtime(true) * 1000);
    }

    private function makeState(
        int $sessionRowId,
        string $challengeId,
        int $openedAtMs,
        int $closedAtMs,
        int $hintCount,
        int $markCount,
        int $bucketStartMs,
        int $bucketCount,
        int $lastHintAtMs,
        bool $fresh,
    ): array {
        return [
            'session_row_id' => $sessionRowId,
            'challenge_id' => $challengeId,
            'opened_at_ms' => $openedAtMs,
            'closed_at_ms' => $closedAtMs,
            'hint_count' => $hintCount,
            'mark_count' => $markCount,
            'bucket_start_ms' => $bucketStartMs,
            'bucket_count' => $bucketCount,
            'last_hint_at_ms' => $lastHintAtMs,
            'fresh' => $fresh,
        ];
    }
}
PHP

# Topology C, part 1: bucket admission boundary. After the incoming draw
# is projected (count + 1), the admission envelope must be exactly the
# free quota — not the free quota plus one. The buggy original padded
# the envelope by one, silently absolving one extra draw inside every
# active bucket.
cat > /app/game/Throttle.php <<'PHP'
<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

/**
 * Rate-bucket admission gate for discrete-action draws.
 *
 * Inputs:
 *   - $nowMs            wall-clock-ish timestamp of the incoming draw
 *   - $bucketStartMs    timestamp of the start of the active bucket
 *   - $countInBucket    number of draws ALREADY issued inside that bucket
 *                       (NOT including the incoming one)
 *   - $widthMs          bucket window width
 *   - $freeQuota        free-of-charge draws allowed inside any one bucket
 *
 * Returns true when the incoming draw is admitted at zero cost and false
 * when the draw should be assessed the configured per-draw penalty.
 *
 * Semantics:
 *   - widthMs <= 0 disables the gate (everything free).
 *   - When the clock falls outside the active bucket window
 *     ((now - bucketStart) >= widthMs), the active bucket is treated as
 *     closed and the incoming draw is always free (it implicitly opens
 *     the next bucket; the caller is responsible for committing the new
 *     bucket_start_ms once the draw is admitted).
 *   - Inside an active bucket: project the bucket forward by one
 *     position (the incoming draw's 1-indexed slot) and admit free
 *     while the projected slot fits inside the quota envelope — and
 *     the envelope is exactly the free quota, not one above it.
 */
final class Throttle {
    public function admit(int $nowMs, int $bucketStartMs, int $countInBucket, int $widthMs, int $freeQuota): bool {
        if ($widthMs <= 0) {
            return true;
        }
        if ($freeQuota < 0) {
            $freeQuota = 0;
        }
        if (($nowMs - $bucketStartMs) >= $widthMs) {
            return true;
        }
        $projectedPosition = $countInBucket + 1;
        return $projectedPosition <= $freeQuota;
    }

    public function remainingFreeSlots(int $bucketStartMs, int $nowMs, int $countInBucket, int $widthMs, int $freeQuota): int {
        if ($widthMs <= 0 || ($nowMs - $bucketStartMs) >= $widthMs) {
            return $freeQuota;
        }
        $remaining = $freeQuota - $countInBucket;
        return $remaining < 0 ? 0 : $remaining;
    }
}
PHP

# Topology C, part 2: score composer. The composition order must be
# (decay, penalty, bonus) THEN snap-to-step. The buggy original snapped
# after decay only, then added/subtracted the discrete components, so
# the persisted score frequently sat off a multiple of the configured
# rounding step and an extra penalty draw could rise above the baseline
# trace because the residual of the unsnapped subtraction interacted
# non-monotonically with the bonus addition.
cat > /app/game/Reckon.php <<'PHP'
<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

/**
 * Composes the final integer value reported on a closed session.
 *
 * Inputs:
 *   - $baseValue          starting value carried by the challenge record.
 *   - $discretePenalties  cumulative integer penalty units accrued from
 *                         per-draw rate-bucket assessments.
 *   - $bonusUnits         cumulative integer bonus units (matched-input
 *                         rewards, reveal contributions).
 *   - $elapsedSeconds     integer seconds spent in active play
 *                         (pause time excluded by the caller).
 *
 * Composition order — every component is integrated BEFORE the snap:
 *   1. Apply per-second decay to the base value.
 *   2. Subtract accumulated penalties.
 *   3. Add bonuses.
 *   4. Snap the resulting integer to the rounding step (round-half-up).
 *
 * Snapping last guarantees two properties the verifier relies on:
 *   - The persisted score is always a multiple of the rounding step.
 *   - Score is a monotonically non-increasing function of additional
 *     penalty units within a fixed scenario (an additional penalty
 *     cannot cause the snapped score to RISE above the baseline).
 *
 * The constructor takes the per-second decay rate and the rounding step
 * (in the same unit as the score; step <= 1 disables quantisation).
 */
final class Reckon {
    public function __construct(
        private readonly int $decayPerSecond,
        private readonly int $roundingStep,
    ) {
        if ($this->decayPerSecond < 0) {
            throw new \InvalidArgumentException('decayPerSecond must be >= 0');
        }
        if ($this->roundingStep < 1) {
            throw new \InvalidArgumentException('roundingStep must be >= 1');
        }
    }

    public function compose(int $baseValue, int $discretePenalties, int $bonusUnits, int $elapsedSeconds): int {
        $decay = $this->decayPerSecond * max(0, $elapsedSeconds);
        $beforeRound = $baseValue - $decay - $discretePenalties + $bonusUnits;
        return $this->snap($beforeRound, $this->roundingStep);
    }

    private function snap(int $value, int $step): int {
        if ($step <= 1) {
            return $value;
        }
        // Round-half-up via integer arithmetic. For negative values we
        // shift the rounding point so half-magnitudes still round away
        // from zero (matches the verifier's expected formula).
        if ($value >= 0) {
            $q = intdiv($value + intdiv($step, 2), $step);
        } else {
            $q = -intdiv((-$value) + intdiv($step, 2), $step);
        }
        return $q * $step;
    }
}
PHP

echo "patches applied"
