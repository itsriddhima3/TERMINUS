<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

use OverlayInspect\Imaging\Coord\AffineWarp;

/**
 * Containment test: given a player-supplied (col, row) input and a list of
 * polygon definitions in source pixel space, return whether the input lands
 * inside any polygon and which one.
 *
 * The (col, row) input is in the rendered cell frame. Classification
 * depends entirely on AffineWarp::cellToPixel for the source pixel;
 * this class only ray-casts polygon vertices (also in source pixels).
 * Edge misses from a folded row axis are a projector issue, not here.
 */
final class Overlap {
    public function __construct(private readonly AffineWarp $warp) {}

    public function classify(int $col, int $row, array $polygons, array $context): array {
        $sw = (int)($context['source_w'] ?? 0);
        $sh = (int)($context['source_h'] ?? 0);
        $fw = (int)($context['fitted_w'] ?? 0);
        $fh = (int)($context['fitted_h'] ?? 0);
        [$u, $v] = $this->warp->cellToPixel($col, $row, $sw, $sh, $fw, $fh);
        if ($u < 0 || $v < 0 || $u >= $sw || $v >= $sh) {
            return ['matched' => false, 'region_id' => null, 'u' => $u, 'v' => $v];
        }
        foreach ($polygons as $poly) {
            if ($this->pointInPolygon((float)$u + 0.5, (float)$v + 0.5, $poly['vertices'] ?? [])) {
                return [
                    'matched' => true,
                    'region_id' => (string)($poly['region_id'] ?? ''),
                    'u' => $u,
                    'v' => $v,
                ];
            }
        }
        return ['matched' => false, 'region_id' => null, 'u' => $u, 'v' => $v];
    }

    private function pointInPolygon(float $x, float $y, array $verts): bool {
        $n = count($verts);
        if ($n < 3) {
            return false;
        }
        $inside = false;
        $j = $n - 1;
        for ($i = 0; $i < $n; $i++) {
            $xi = (float)$verts[$i][0];
            $yi = (float)$verts[$i][1];
            $xj = (float)$verts[$j][0];
            $yj = (float)$verts[$j][1];
            $crosses = (($yi > $y) !== ($yj > $y))
                && ($x < ($xj - $xi) * ($y - $yi) / ($yj - $yi + 0.000000001) + $xi);
            if ($crosses) {
                $inside = !$inside;
            }
            $j = $i;
        }
        return $inside;
    }
}
