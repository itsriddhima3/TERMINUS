<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging\Coord;

/**
 * Coordinate transformer between source pixel space and terminal cell space.
 *
 * The caller supplies the source frame dimensions (sw, sh) and the rendered
 * frame dimensions (tw, th) in cells. The constructor receives the cell
 * aspect (width-over-height) for terminal cells, which is generally < 1.0
 * because most monospace fonts produce taller-than-wide cells.
 *
 * The forward map (pixelToCell) takes (u, v) in source pixels and returns
 * (col, row) in cell space. The inverse (cellToPixel) goes the other way.
 *
 * Note: tw and th are the *fitted* render dimensions from Stretch (aspect
 * already baked into fitted_w / fitted_h). Forward and inverse maps must
 * be symmetric linear scale on col and row using (sw, sh, tw, th) only.
 * The stored cellAspect ratio is for display helpers; it must not enter
 * pixelToCell or cellToPixel or row indices double-count aspect.
 */
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
        // Source pixel -> rendered cell within the fitted rectangle.
        // tw/th already reflect the aspect-preserving fit from Stretch.
        $col = (int)floor($u * $tw / $sw);
        $row = (int)floor($v * $th / $sh * $this->cellAspect);
        return [$col, $row];
    }

    public function cellToPixel(int $col, int $row, int $sw, int $sh, int $tw, int $th): array {
        if ($sw <= 0 || $sh <= 0 || $tw <= 0 || $th <= 0) {
            return [0, 0];
        }
        // Rendered cell within fitted rectangle -> source pixel.
        // Inverse of pixelToCell over the same (sw, sh, tw, th) tuple.
        $u = (int)floor($col * $sw / $tw);
        $v = (int)floor($row * $sh / $th * $this->cellAspect);
        return [$u, $v];
    }
}
