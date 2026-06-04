<?php
declare(strict_types=1);

namespace OverlayInspect\Persistence;

use PDO;

final class Audit {
    public function __construct(private readonly PDO $pdo) {}

    public function record(string $action, ?string $detail = null): int {
        $now = (int)(microtime(true) * 1000);
        $stmt = $this->pdo->prepare(
            'INSERT INTO audit_log (occurred_at_ms, action, detail) VALUES (?, ?, ?)'
        );
        $stmt->execute([$now, $action, $detail]);
        return (int)$this->pdo->lastInsertId();
    }

    public function recentActions(int $limit = 20): array {
        $stmt = $this->pdo->prepare(
            'SELECT * FROM audit_log ORDER BY audit_row_id DESC LIMIT ?'
        );
        $stmt->execute([$limit]);
        return $stmt->fetchAll();
    }
}
