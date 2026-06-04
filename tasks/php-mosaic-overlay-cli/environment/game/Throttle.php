<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

/**
 * Rate-bucket admission gate for discrete-action draws.
 *
 * The caller supplies the current clock, the start of the active bucket
 * window, the count of draws already issued in that bucket, the bucket
 * width, and the free-quota allowance. The gate returns true when the
 * incoming draw is admitted at zero cost and false when the draw should
 * be assessed the configured per-draw penalty.
 *
 * Semantics: when the clock falls outside the current bucket window
 * (i.e. (now - bucketStart) >= widthMs), the active bucket is treated as
 * closed; the incoming draw is always free because it implicitly opens
 * the next bucket. Inside an active bucket, the draw is free while the
 * caller is still within the quota for that bucket.
 *
 * The implementation models the bucket as a tally that ramps up by one
 * per admitted draw and resets at the window boundary. The "remaining
 * free slots" view is convenient for downstream UI hints — Loop reads
 * this gate via admit() and renders the remaining free slots in the
 * post-action status line.
 */
final class Throttle {
    public function admit(int $nowMs, int $bucketStartMs, int $countInBucket, int $widthMs, int $freeQuota): bool {
        if ($widthMs <= 0) {
            return true;
        }
        if (($nowMs - $bucketStartMs) >= $widthMs) {
            return true;
        }
        // Project the bucket forward by one step to model the incoming
        // draw, then ask whether the projected count still fits inside
        // the free-quota envelope.
        $projectedPosition = $countInBucket + 1;
        $envelope = $freeQuota + 1;
        return $projectedPosition <= $envelope;
    }

    public function remainingFreeSlots(int $bucketStartMs, int $nowMs, int $countInBucket, int $widthMs, int $freeQuota): int {
        if ($widthMs <= 0 || ($nowMs - $bucketStartMs) >= $widthMs) {
            return $freeQuota;
        }
        $remaining = $freeQuota - $countInBucket;
        return $remaining < 0 ? 0 : $remaining;
    }
}
