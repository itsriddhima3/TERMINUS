<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Coord;

/**
 * Polar-coordinate helper used by the overlay-help renderer to lay out
 * caption arcs around a region's anchor point.
 *
 * The renderer asks for points at angular intervals around a centre cell;
 * because terminal cells are non-square, the conversion from a notional
 * isotropic radius (in source-pixel units) to a (col, row) cell offset
 * has to compensate for the cell aspect (width-over-height). The class
 * is not on the gameplay coordinate path — it is only invoked from the
 * overlay-help subcommand, which renders a static help frame.
 */
final class Polar {
    public function __construct(private readonly float $cellAspect) {
        if ($this->cellAspect <= 0.0) {
            throw new \InvalidArgumentException('cellAspect must be positive');
        }
    }

    public function pointAt(int $centreCol, int $centreRow, float $radiusPx, float $angleRad, int $sw, int $sh, int $tw, int $th): array {
        if ($sw <= 0 || $sh <= 0 || $tw <= 0 || $th <= 0) {
            return [$centreCol, $centreRow];
        }
        $du = (int)round($radiusPx * cos($angleRad));
        $dv = (int)round($radiusPx * sin($angleRad));
        $dCol = (int)round($du * $tw / $sw);
        $dRow = (int)round($dv * $th / $sh * $this->cellAspect);
        $col = $centreCol + $dCol;
        $row = $centreRow + $dRow;
        if ($col < 0) { $col = 0; }
        if ($row < 0) { $row = 0; }
        if ($col >= $tw) { $col = $tw - 1; }
        if ($row >= $th) { $row = $th - 1; }
        return [$col, $row];
    }

    public function arc(int $centreCol, int $centreRow, float $radiusPx, int $segments, int $sw, int $sh, int $tw, int $th): array {
        if ($segments <= 0) {
            return [];
        }
        $points = [];
        $step = (2.0 * M_PI) / $segments;
        for ($i = 0; $i < $segments; $i++) {
            $points[] = $this->pointAt($centreCol, $centreRow, $radiusPx, $i * $step, $sw, $sh, $tw, $th);
        }
        return $points;
    }

    public function cellAspect(): float {
        return $this->cellAspect;
    }
}
