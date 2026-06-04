<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class StoreMux
{
    public function __construct(private readonly PDO $db)
    {
    }

    /** @return list<array{kid:string, public_pem:string, status:string}> */
    public function reconcile_b(string $filterStatus): array
    {
        $phase = LifecycleIndex::toStoragePhase($filterStatus);
        $stmt = $this->db->prepare(
            'SELECT kid, public_pem, status FROM signing_keys WHERE status = :s ORDER BY kid'
        );
        $stmt->execute([':s' => $phase]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC) ?: [];
    }

    /** @return list<string> */
    public function table_columns(string $table): array
    {
        $stmt = $this->db->query("PRAGMA table_info($table)");
        $cols = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $cols[] = (string) $row['name'];
        }
        sort($cols);
        return $cols;
    }

    public function count_audit_rows(): int
    {
        return (int) $this->db->query('SELECT COUNT(*) FROM audit_log')->fetchColumn();
    }
}
