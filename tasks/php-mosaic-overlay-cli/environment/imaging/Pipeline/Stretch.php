<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Pipeline;

/**
 * Aspect-preserving fit of a source pixel buffer to a target cell grid.
 *
 * Given a source buffer (intensity row-major) and a target grid (cols x rows)
 * along with the cell aspect (width-over-height), compute the largest
 * rectangle inside the target grid that preserves the source aspect ratio,
 * then nearest-neighbour resample the source into that fitted rectangle.
 *
 * Returns:
 *   [
 *     'cells'    => int[] row-major intensity values, length fitted_w * fitted_h
 *     'fitted_w' => int   actual width in cells of the rendered rectangle
 *     'fitted_h' => int   actual height in cells of the rendered rectangle
 *   ]
 */
final class Stretch {
    public function __construct(private readonly float $cellAspect) {
        if ($this->cellAspect <= 0.0) {
            throw new \InvalidArgumentException('cellAspect must be positive');
        }
    }

    public function apply(array $src, int $tgtW, int $tgtH): array {
        $sw = (int)($src['source_width'] ?? 0);
        $sh = (int)($src['source_height'] ?? 0);
        $pixels = $src['pixels'] ?? [];
        if ($sw <= 0 || $sh <= 0 || $tgtW <= 0 || $tgtH <= 0) {
            return ['cells' => [], 'fitted_w' => 0, 'fitted_h' => 0];
        }
        // Each cell occupies cellAspect units horizontally and 1 unit
        // vertically in visual space. Compute the largest uniform scale
        // (visual-units per source-pixel) that keeps the rendered image
        // inside the target grid.
        $unitsPerPxByWidth = ($tgtW * $this->cellAspect) / $sw;
        $unitsPerPxByHeight = $tgtH / $sh;
        $scale = min($unitsPerPxByWidth, $unitsPerPxByHeight);

        $fittedW = (int)max(1, round(($sw * $scale) / $this->cellAspect));
        $fittedH = (int)max(1, round($sh * $scale));
        if ($fittedW > $tgtW) {
            $fittedW = $tgtW;
        }
        if ($fittedH > $tgtH) {
            $fittedH = $tgtH;
        }

        $cells = [];
        for ($r = 0; $r < $fittedH; $r++) {
            $vBase = (int)floor(($r + 0.5) * $sh / $fittedH);
            if ($vBase >= $sh) { $vBase = $sh - 1; }
            for ($c = 0; $c < $fittedW; $c++) {
                $u = (int)floor(($c + 0.5) * $sw / $fittedW);
                if ($u >= $sw) { $u = $sw - 1; }
                $cells[] = $pixels[$vBase * $sw + $u] ?? 0;
            }
        }
        return [
            'cells' => $cells,
            'fitted_w' => $fittedW,
            'fitted_h' => $fittedH,
        ];
    }
}
