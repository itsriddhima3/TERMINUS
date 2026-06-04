<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class KeyPromoter
{
    public static function insertActive(
        PDO $db,
        string $kid,
        string $pubPem,
        string $privPem,
        string $createdAt,
    ): void {
        $ins = $db->prepare(
            'INSERT INTO signing_keys (kid, public_pem, private_pem, status, created_at)
             VALUES (:kid, :pub, :priv, :status, :ts)'
        );
        $ins->execute([
            ':kid' => $kid,
            ':pub' => $pubPem,
            ':priv' => $privPem,
            ':status' => 'active',
            ':ts' => $createdAt,
        ]);
    }
}
