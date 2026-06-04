<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class KeyMaterial
{
    public static function publicPemForKid(PDO $db, string $kid): ?string
    {
        if ($kid === '') {
            return null;
        }
        $stmt = $db->prepare(
            "SELECT public_pem FROM signing_keys WHERE kid = :kid AND status = 'active'"
        );
        $stmt->execute([':kid' => $kid]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row ? (string) $row['public_pem'] : null;
    }

    /** @internal overlap-window lookup; not wired into TokenGate today */
    public static function publicPemForKidOverlap(PDO $db, string $kid): ?string
    {
        if ($kid === '') {
            return null;
        }
        $stmt = $db->prepare(
            "SELECT public_pem FROM signing_keys WHERE kid = :kid AND status IN ('active','previous')"
        );
        $stmt->execute([':kid' => $kid]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row ? (string) $row['public_pem'] : null;
    }
}
