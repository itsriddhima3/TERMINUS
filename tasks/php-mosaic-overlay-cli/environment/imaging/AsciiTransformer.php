<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging;

/**
 * Greyscale pixel intensity to ASCII glyph mapper.
 *
 * Each intensity 0..255 is bucketed into one of the palette indices.
 * Darker pixels map to denser glyphs (later in the palette string).
 */
final class AsciiTransformer {
    public function __construct(private readonly string $palette) {
        if ($this->palette === '') {
            throw new \InvalidArgumentException('palette must be non-empty');
        }
    }

    public function transform(array $cellBuffer, int $cols, int $rows): array {
        $len = strlen($this->palette);
        $out = [];
        for ($r = 0; $r < $rows; $r++) {
            $line = '';
            for ($c = 0; $c < $cols; $c++) {
                $idx = $r * $cols + $c;
                $px = $cellBuffer[$idx] ?? 255;
                $bucket = $len - 1 - (int)floor($px * $len / 256);
                if ($bucket < 0) {
                    $bucket = 0;
                }
                if ($bucket >= $len) {
                    $bucket = $len - 1;
                }
                $line .= $this->palette[$bucket];
            }
            $out[] = $line;
        }
        return $out;
    }
}
