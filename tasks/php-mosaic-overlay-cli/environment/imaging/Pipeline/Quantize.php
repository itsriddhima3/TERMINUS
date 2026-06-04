<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Pipeline;

/**
 * Greyscale intensity quantizer.
 *
 * Reduces an 8-bit grey buffer to N quantization levels. The downstream
 * AsciiTransformer then maps each level to a glyph. Splitting the
 * quantization step from the glyph mapping lets the describe sub-command
 * dump the level histogram without touching the glyph palette.
 */
final class Quantize {
    public function apply(array $pixels, int $levels): array {
        if ($levels < 2) {
            throw new \InvalidArgumentException('levels must be >= 2');
        }
        $step = max(1, (int)floor(256 / $levels));
        $out = [];
        foreach ($pixels as $p) {
            $b = (int)floor($p / $step);
            if ($b >= $levels) { $b = $levels - 1; }
            $out[] = $b * $step;
        }
        return $out;
    }

    public function histogram(array $pixels, int $levels): array {
        $bins = array_fill(0, $levels, 0);
        $step = max(1, (int)floor(256 / $levels));
        foreach ($pixels as $p) {
            $b = (int)floor($p / $step);
            if ($b >= $levels) { $b = $levels - 1; }
            $bins[$b]++;
        }
        return $bins;
    }
}
