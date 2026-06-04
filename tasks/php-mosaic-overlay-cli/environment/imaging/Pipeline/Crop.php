<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Pipeline;

/**
 * Pixel-buffer cropper used by the help-screen preview renderer.
 *
 * Extracts a rectangular sub-region from a row-major source buffer
 * and returns a new tightly-packed sub-buffer. Not used on the play
 * loop path; the play loop renders entire scenes via Stretch.
 */
final class Crop {
    public function apply(array $pixels, int $srcW, int $srcH, int $x, int $y, int $w, int $h): array {
        if ($x < 0 || $y < 0 || $x + $w > $srcW || $y + $h > $srcH) {
            throw new \InvalidArgumentException('crop region out of bounds');
        }
        $out = [];
        for ($r = 0; $r < $h; $r++) {
            $rowBase = ($y + $r) * $srcW + $x;
            for ($c = 0; $c < $w; $c++) {
                $out[] = $pixels[$rowBase + $c];
            }
        }
        return $out;
    }
}
