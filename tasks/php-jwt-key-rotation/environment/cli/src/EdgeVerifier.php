<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

/** Alternate RS256 path — not on the guardctl hot path. */
final class EdgeVerifier
{
    public function __construct(private readonly PDO $db)
    {
    }

    public function tryAccept(string $token): bool
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3 || $parts[2] === '') {
            return false;
        }
        [$h64, $p64, $s64] = $parts;
        $header = json_decode($this->b64url($h64, true), true) ?? [];
        $payload = json_decode($this->b64url($p64, true), true) ?? [];
        $kid = (string) ($header['kid'] ?? '');
        if (($header['alg'] ?? '') !== 'RS256' || ($payload['iss'] ?? '') !== 'vault-edge') {
            return false;
        }
        $pub = KeyMaterial::publicPemForKidOverlap($this->db, $kid);
        if ($pub === null) {
            return false;
        }
        $data = $h64 . '.' . $p64;
        $sig = $this->b64url($s64, true);
        if (openssl_verify($data, $sig, $pub, OPENSSL_ALGO_SHA256) !== 1) {
            return false;
        }
        $now = time();
        return (int) ($payload['nbf'] ?? 0) <= $now && (int) ($payload['exp'] ?? 0) >= $now;
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
