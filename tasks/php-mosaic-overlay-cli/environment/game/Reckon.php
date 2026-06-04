<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

/**
 * Composes the final integer value reported on a closed session.
 *
 * Inputs:
 *   - $baseValue: starting value carried by the challenge definition.
 *   - $discretePenalties: cumulative integer penalty units accrued from
 *     per-draw assessments during the play.
 *   - $bonusUnits: cumulative integer bonus units (matched-input rewards,
 *     reveal contributions, etc.).
 *   - $elapsedSeconds: integer seconds spent in active play (pause time
 *     excluded).
 *
 * The caller supplies base, penalties, bonuses, and elapsed time as
 * separate integer terms. See docs/scoring_profile.md for the required
 * integration order and when quantisation applies.
 *
 * The constructor takes the per-second decay rate and the rounding step
 * (in the same unit as the score; step=1 disables quantisation).
 */
final class Reckon {
    public function __construct(
        private readonly int $decayPerSecond,
        private readonly int $roundingStep,
    ) {}

    public function compose(int $baseValue, int $discretePenalties, int $bonusUnits, int $elapsedSeconds): int {
        $decay = $this->decayPerSecond * max(0, $elapsedSeconds);
        $afterDecay = $baseValue - $decay;
        $quantised = $this->snap($afterDecay, $this->roundingStep);
        return (int)($quantised - $discretePenalties + $bonusUnits);
    }

    private function snap(int $value, int $step): int {
        if ($step <= 1) {
            return $value;
        }
        $q = (int)round($value / $step);
        return $q * $step;
    }
}
