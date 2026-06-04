<?php
declare(strict_types=1);

namespace OverlayInspect\Persistence;

use PDO;

final class Schema {
    private const REQUIRED_TABLES = [
        'packs',
        'challenges',
        'region_defs',
        'sessions',
        'marks',
        'hints',
        'audit_log',
    ];

    public static function ensure(PDO $pdo): void {
        $existing = [];
        $stmt = $pdo->query("SELECT name FROM sqlite_master WHERE type='table'");
        foreach ($stmt->fetchAll() as $row) {
            $existing[(string)$row['name']] = true;
        }
        $missing = [];
        foreach (self::REQUIRED_TABLES as $t) {
            if (!isset($existing[$t])) {
                $missing[] = $t;
            }
        }
        if (!empty($missing)) {
            throw new \RuntimeException('database missing tables: ' . implode(',', $missing));
        }
    }
}
