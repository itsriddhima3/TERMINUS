<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

final class Throttle {
    public function admit(int $nowMs, int $bucketStartMs, int $countInBucket, int $widthMs, int $freeQuota): bool {
        if ($widthMs <= 0) {
            return true;
        }
        if (($nowMs - $bucketStartMs) >= $widthMs) {
            return true;
        }
        return $countInBucket < $freeQuota;
    }
}
