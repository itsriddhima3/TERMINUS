<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Coord;

final class AffineWarp {
    public function __construct(private readonly float $cellAspect) {
        if ($this->cellAspect <= 0.0) {
            throw new \InvalidArgumentException('cellAspect must be positive');
        }
    }

    public function pixelToCell(int $u, int $v, int $sw, int $sh, int $tw, int $th): array {
        if ($sw <= 0 || $sh <= 0 || $tw <= 0 || $th <= 0) {
            return [0, 0];
        }
        $col = (int)floor($u * $tw / $sw);
        $row = (int)floor($v * $th / $sh);
        return [$col, $row];
    }

    public function cellToPixel(int $col, int $row, int $sw, int $sh, int $tw, int $th): array {
        if ($sw <= 0 || $sh <= 0 || $tw <= 0 || $th <= 0) {
            return [0, 0];
        }
        $u = (int)floor($col * $sw / $tw);
        $v = (int)floor($row * $sh / $th);
        return [$u, $v];
    }
}
