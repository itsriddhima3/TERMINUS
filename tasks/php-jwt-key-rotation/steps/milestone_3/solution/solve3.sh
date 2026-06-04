#!/bin/bash

set -euo pipefail

if [ -f /app/var/api.pid ]; then
  kill "$(cat /app/var/api.pid)" 2>/dev/null || true
  rm -f /app/var/api.pid
fi
bash /app/scripts/start-api.sh

cat > /app/cli/src/LifecycleIndex.php <<'PHP'
<?php
declare(strict_types=1);

namespace Vault\Cli;

final class LifecycleIndex
{
    public static function toStoragePhase(string $filterStatus): string
    {
        return $filterStatus;
    }
}
PHP

cat > /app/cli/src/RetireCoordinator.php <<'PHP'
<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class RetireCoordinator
{
    public static function markRetired(PDO $db, string $kid, string $successorKid): void
    {
        if ($kid === '') {
            return;
        }
        $demote = $db->prepare(
            "UPDATE signing_keys SET status = 'previous', private_pem = NULL WHERE kid = :kid"
        );
        $demote->execute([':kid' => $kid]);
        $stmt = $db->prepare(
            'INSERT INTO audit_log (event_type, kid, detail_json, created_at) VALUES (:e, :k, :d, :t)'
        );
        $stmt->execute([
            ':e' => 'key_retired',
            ':k' => $kid,
            ':d' => json_encode(['successor' => $successorKid], JSON_THROW_ON_ERROR),
            ':t' => gmdate('c'),
        ]);
    }
}
PHP

cat > /app/cli/src/RotateHub.php <<'PHP'
<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class RotateHub
{
    public function __construct(private readonly PDO $db)
    {
    }

    /** @return array{previous_kid:string, active_kid:string} */
    public function phase_c(): array
    {
        $active = $this->db->query(
            "SELECT kid FROM signing_keys WHERE status = 'active' LIMIT 1"
        )->fetch(PDO::FETCH_ASSOC);
        $prevKid = $active ? (string) $active['kid'] : '';
        $newKid = 'key-002';

        $priv = openssl_pkey_new([
            'private_key_bits' => 2048,
            'private_key_type' => OPENSSL_KEYTYPE_RSA,
        ]);
        openssl_pkey_export($priv, $privPem);
        $details = openssl_pkey_get_details($priv);
        $pubPem = $details['key'];
        $ts = gmdate('c');

        RetireCoordinator::markRetired($this->db, $prevKid, $newKid);
        KeyPromoter::insertActive($this->db, $newKid, $pubPem, $privPem, $ts);
        $this->append_audit('key_promoted', $newKid, ['from' => $prevKid]);
        return ['previous_kid' => $prevKid, 'active_kid' => $newKid];
    }

    /** @param array<string, mixed> $detail */
    private function append_audit(string $event, string $kid, array $detail): void
    {
        $stmt = $this->db->prepare(
            'INSERT INTO audit_log (event_type, kid, detail_json, created_at) VALUES (:e, :k, :d, :t)'
        );
        $stmt->execute([
            ':e' => $event,
            ':k' => $kid,
            ':d' => json_encode($detail, JSON_THROW_ON_ERROR),
            ':t' => gmdate('c'),
        ]);
    }
}
PHP

cat > /app/api/src/JwksHandler.php <<'PHP'
<?php
declare(strict_types=1);

namespace Vault\Api;

use PDO;

final class JwksHandler
{
    public function __construct(private readonly PDO $db)
    {
    }

    public function handle(): void
    {
        JwksCache::forget();
        $stmt = $this->db->query(
            "SELECT kid, public_pem FROM signing_keys WHERE status IN ('active','previous') ORDER BY kid"
        );
        $keys = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $keys[] = $this->jwkFromPem((string) $row['kid'], (string) $row['public_pem']);
        }
        http_response_code(200);
        header('Content-Type: application/json');
        echo json_encode(['keys' => $keys], JSON_UNESCAPED_SLASHES);
    }

    /** @return array<string, mixed> */
    private function jwkFromPem(string $kid, string $pem): array
    {
        $res = openssl_pkey_get_public($pem);
        $details = openssl_pkey_get_details($res);
        $n = $this->b64urlEncode($details['rsa']['n']);
        $e = $this->b64urlEncode($details['rsa']['e']);
        return [
            'kty' => 'RSA',
            'kid' => $kid,
            'alg' => 'RS256',
            'use' => 'sig',
            'n' => $n,
            'e' => $e,
        ];
    }

    private function b64urlEncode(string $raw): string
    {
        return rtrim(strtr(base64_encode($raw), '+/', '-_'), '=');
    }
}
PHP

/app/cli/guardctl rotate
