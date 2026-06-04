<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

/**
 * Per-challenge entry gate used by the play loop only to decide whether
 * a new session may be opened against a given challenge id.
 *
 * The gate is independent of the per-action rate bucket (see Throttle).
 * It applies a coarse per-day allowance to limit how often the same
 * challenge can be re-opened — a UX guard rather than a scoring input.
 * No rows it writes feed into the score composition path.
 */
final class Gate {
    public function admit(int $nowMs, int $previousOpenAtMs, int $cooldownMs, int $freeQuotaPerDay, int $todayOpenCount): bool {
        if ($cooldownMs < 0) {
            $cooldownMs = 0;
        }
        if ($freeQuotaPerDay < 0) {
            $freeQuotaPerDay = 0;
        }
        $sincePrev = $nowMs - $previousOpenAtMs;
        if ($previousOpenAtMs > 0 && $sincePrev < $cooldownMs) {
            return false;
        }
        return $todayOpenCount < $freeQuotaPerDay;
    }

    public function nextEligibleMs(int $previousOpenAtMs, int $cooldownMs): int {
        if ($previousOpenAtMs <= 0) {
            return 0;
        }
        return $previousOpenAtMs + max(0, $cooldownMs);
    }
}
