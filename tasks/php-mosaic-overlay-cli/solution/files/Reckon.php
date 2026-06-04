<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

final class Reckon {
    public function __construct(
        private readonly int $decayPerSecond,
        private readonly int $roundingStep,
    ) {}

    public function compose(int $baseValue, int $discretePenalties, int $bonusUnits, int $elapsedSeconds): int {
        $decay = $this->decayPerSecond * max(0, $elapsedSeconds);
        $beforeRound = $baseValue - $decay - $discretePenalties + $bonusUnits;
        return $this->snap($beforeRound, $this->roundingStep);
    }

    private function snap(int $value, int $step): int {
        if ($step <= 1) {
            return $value;
        }
        $q = (int)round($value / $step);
        return $q * $step;
    }
}
