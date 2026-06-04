<?php
declare(strict_types=1);

namespace OverlayInspect\Game;

use PDO;

/**
 * Reads challenge definitions from the database and the on-disk assets
 * the seeded rows reference. The loader returns a structured snapshot
 * that the engine uses for the duration of a single play.
 */
final class PackLoader {
    public function __construct(
        private readonly PDO $pdo,
        private readonly string $appRoot,
    ) {}

    public function loadChallenge(string $challengeId): array {
        $stmt = $this->pdo->prepare('SELECT * FROM challenges WHERE challenge_id = ?');
        $stmt->execute([$challengeId]);
        $challenge = $stmt->fetch();
        if ($challenge === false) {
            throw new \RuntimeException("unknown challenge id: {$challengeId}");
        }
        $regStmt = $this->pdo->prepare(
            'SELECT * FROM region_defs WHERE challenge_id = ? ORDER BY region_id ASC'
        );
        $regStmt->execute([$challengeId]);
        $polygons = [];
        foreach ($regStmt->fetchAll() as $row) {
            $verts = json_decode((string)$row['polygon_json'], true, 512, JSON_THROW_ON_ERROR);
            $polygons[] = [
                'region_id' => (string)$row['region_id'],
                'region_label' => (string)$row['region_label'],
                'vertices' => $verts,
            ];
        }
        $sceneA = rtrim($this->appRoot, '/') . '/' . ltrim((string)$challenge['scene_a_path'], '/');
        $sceneB = rtrim($this->appRoot, '/') . '/' . ltrim((string)$challenge['scene_b_path'], '/');
        return [
            'challenge_id' => (string)$challenge['challenge_id'],
            'pack_id' => (string)$challenge['pack_id'],
            'source_width' => (int)$challenge['source_width'],
            'source_height' => (int)$challenge['source_height'],
            'base_units' => (int)$challenge['base_units'],
            'scene_a_abs_path' => $sceneA,
            'scene_b_abs_path' => $sceneB,
            'polygons' => $polygons,
        ];
    }

    public function listChallenges(): array {
        $stmt = $this->pdo->query(
            'SELECT challenge_id, pack_id, source_width, source_height FROM challenges ORDER BY challenge_id ASC'
        );
        return $stmt->fetchAll();
    }
}
