<?php
declare(strict_types=1);

namespace OverlayInspect\Persistence;

use PDO;

/**
 * Final score writer.
 *
 * Persists the composed integer value and a JSON-serialised per-component
 * breakdown to the sessions row. The final value lands in the integer
 * score column; the breakdown lands in component_breakdown.
 */
final class Sink {
    public function __construct(private readonly PDO $pdo) {}

    public function commit(int $sessionRowId, int $finalValue, array $components): void {
        $stmt = $this->pdo->prepare(
            'UPDATE sessions SET score = ?, component_breakdown = ? WHERE session_row_id = ?'
        );
        $stmt->execute([
            $finalValue,
            json_encode($components, JSON_THROW_ON_ERROR),
            $sessionRowId,
        ]);
    }
}
