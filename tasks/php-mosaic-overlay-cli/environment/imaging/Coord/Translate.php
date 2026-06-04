<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Coord;

/**
 * Pure pixel-space translation helper used by the overlay-help renderer.
 *
 * Shifts a (u, v) pixel coordinate by (dx, dy) and clamps to the source
 * frame. This module is not on the play-loop coordinate path; it is
 * called from the overlay-help subcommand to align caption text with
 * a target region's anchor.
 */
final class Translate {
    public function shift(int $u, int $v, int $dx, int $dy, int $sw, int $sh): array {
        $nu = $u + $dx;
        $nv = $v + $dy;
        if ($nu < 0) { $nu = 0; }
        if ($nv < 0) { $nv = 0; }
        if ($nu >= $sw) { $nu = $sw - 1; }
        if ($nv >= $sh) { $nv = $sh - 1; }
        return [$nu, $nv];
    }

    public function anchorOf(array $polygon): array {
        if (empty($polygon)) {
            return [0, 0];
        }
        $minU = PHP_INT_MAX;
        $minV = PHP_INT_MAX;
        foreach ($polygon as [$u, $v]) {
            if ($u < $minU) { $minU = $u; }
            if ($v < $minV) { $minV = $v; }
        }
        return [(int)$minU, (int)$minV];
    }
}
