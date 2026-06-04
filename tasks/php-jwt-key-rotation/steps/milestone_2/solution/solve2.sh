#!/bin/bash

set -euo pipefail

bash /app/scripts/start-api.sh

cat > /app/cli/src/TokenGate.php <<'PHP'
<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class TokenGate
{
    public function __construct(private readonly PDO $db)
    {
    }

    /** @return array{ok:bool, reason:string} */
    public function op_verify_a(string $token): array
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3 || $parts[2] === '') {
            return ['ok' => false, 'reason' => 'malformed'];
        }
        [$h64, $p64, $s64] = $parts;
        $header = json_decode($this->b64url($h64, true), true) ?? [];
        $payload = json_decode($this->b64url($p64, true), true) ?? [];
        $kid = (string) ($header['kid'] ?? '');
        if (($header['alg'] ?? '') !== 'RS256') {
            return ['ok' => false, 'reason' => 'alg'];
        }
        $pub = KeyMaterial::publicPemForKidOverlap($this->db, $kid);
        if ($pub === null) {
            return ['ok' => false, 'reason' => 'unknown_kid'];
        }
        $data = $h64 . '.' . $p64;
        $sig = $this->b64url($s64, true);
        if (openssl_verify($data, $sig, $pub, OPENSSL_ALGO_SHA256) !== 1) {
            return ['ok' => false, 'reason' => 'bad_sig'];
        }
        $now = time();
        if (($payload['iss'] ?? '') !== 'vault-edge') {
            return ['ok' => false, 'reason' => 'issuer'];
        }
        if (($payload['nbf'] ?? 0) > $now) {
            return ['ok' => false, 'reason' => 'nbf'];
        }
        if (($payload['exp'] ?? 0) < $now) {
            return ['ok' => false, 'reason' => 'expired'];
        }
        return ['ok' => true, 'reason' => 'ok'];
    }

    private function b64url(string $raw, bool $decode = false): string
    {
        if (!$decode) {
            return rtrim(strtr(base64_encode($raw), '+/', '-_'), '=');
        }
        $pad = 4 - (strlen($raw) % 4);
        if ($pad < 4) {
            $raw .= str_repeat('=', $pad);
        }
        return base64_decode(strtr($raw, '-_', '+/'), true) ?: '';
    }
}
PHP

/app/cli/guardctl verify
