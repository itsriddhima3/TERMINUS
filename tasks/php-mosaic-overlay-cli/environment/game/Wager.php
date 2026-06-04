<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

/**
 * Pre-play wager helper used by the describe sub-command to preview the
 * configured scoring profile for a challenge.
 *
 * Given a configured base value, a per-second decay rate, a rounding
 * step and a peek-bonus, compose a quick estimate of what the player
 * would score for a perfect run completed within a target deadline.
 * This module is not on the gameplay scoring path — Reckon composes
 * the actual closed-session score. Wager exists to render a
 * "potential score: NNN" line in the describe output and to power
 * the offline scoring-profile audit tooling.
 */
final class Wager {
    public function __construct(
        private readonly int $decayPerSecond,
        private readonly int $roundingStep,
        private readonly int $peekBonus,
    ) {
        if ($this->roundingStep < 1) {
            throw new \InvalidArgumentException('roundingStep must be >= 1');
        }
    }

    public function estimate(int $baseValue, int $deadlineSeconds, int $expectedMatches): int {
        $decay = $this->decayPerSecond * max(0, $deadlineSeconds);
        $bonus = max(0, $expectedMatches) * $this->peekBonus;
        $before = $baseValue - $decay + $bonus;
        return $this->snap($before, $this->roundingStep);
    }

    public function decayCurve(int $baseValue, int $deadlineSeconds, int $step): array {
        if ($step <= 0) {
            return [];
        }
        $samples = [];
        for ($t = 0; $t <= $deadlineSeconds; $t += $step) {
            $samples[$t] = $this->snap($baseValue - $this->decayPerSecond * $t, $this->roundingStep);
        }
        return $samples;
    }

    private function snap(int $value, int $step): int {
        if ($step <= 1) {
            return $value;
        }
        if ($value >= 0) {
            $q = intdiv($value + intdiv($step, 2), $step);
        } else {
            $q = -intdiv((-$value) + intdiv($step, 2), $step);
        }
        return $q * $step;
    }
}
