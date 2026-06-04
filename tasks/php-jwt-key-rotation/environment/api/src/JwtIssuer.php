<?php
declare(strict_types=1);

namespace Vault\Api;

use PDO;

final class JwtIssuer
{
    public function __construct(private readonly PDO $db, private readonly array $cfg)
    {
    }

    public function issue(string $subject): string
    {
        $row = $this->activeKey();
        $now = time();
        $payload = [
            'iss' => $this->cfg['issuer'],
            'sub' => $subject,
            'iat' => $now,
            'exp' => $now + (int) $this->cfg['token_ttl'],
        ];
        return $this->encode($payload, $row['kid'], $row['private_pem']);
    }

    public function verify(string $token): array
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3) {
            throw new \RuntimeException('malformed');
        }
        [$h64, $p64, $s64] = $parts;
        $header = json_decode($this->b64urlDecode($h64), true, 512, JSON_THROW_ON_ERROR);
        $payload = json_decode($this->b64urlDecode($p64), true, 512, JSON_THROW_ON_ERROR);
        $kid = (string) ($header['kid'] ?? '');
        $pub = $this->publicPemForKid($kid);
        $data = $h64 . '.' . $p64;
        $sig = $this->b64urlDecode($s64);
        $ok = openssl_verify($data, $sig, $pub, OPENSSL_ALGO_SHA256);
        if ($ok !== 1) {
            throw new \RuntimeException('bad_sig');
        }
        $now = time();
        if (($payload['iss'] ?? '') !== $this->cfg['issuer']) {
            throw new \RuntimeException('issuer');
        }
        if (($payload['nbf'] ?? 0) > $now) {
            throw new \RuntimeException('nbf');
        }
        if (($payload['exp'] ?? 0) < $now) {
            throw new \RuntimeException('expired');
        }
        return $payload;
    }

    /** @return array{kid: string, private_pem: string, public_pem: string} */
    private function activeKey(): array
    {
        $stmt = $this->db->query(
            "SELECT kid, private_pem, public_pem FROM signing_keys WHERE status = 'active' LIMIT 1"
        );
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$row || empty($row['private_pem'])) {
            throw new \RuntimeException('no_active_key');
        }
        return $row;
    }

    private function publicPemForKid(string $kid): string
    {
        $stmt = $this->db->prepare(
            "SELECT public_pem FROM signing_keys WHERE kid = :kid AND status IN ('active','previous')"
        );
        $stmt->execute([':kid' => $kid]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$row) {
            throw new \RuntimeException('unknown_kid');
        }
        return (string) $row['public_pem'];
    }

    /** @param array<string, mixed> $payload */
    private function encode(array $payload, string $kid, string $privatePem): string
    {
        $header = ['alg' => 'RS256', 'typ' => 'JWT', 'kid' => $kid];
        $h = $this->b64urlEncode(json_encode($header, JSON_THROW_ON_ERROR));
        $p = $this->b64urlEncode(json_encode($payload, JSON_THROW_ON_ERROR));
        $data = $h . '.' . $p;
        $sig = '';
        openssl_sign($data, $sig, $privatePem, OPENSSL_ALGO_SHA256);
        return $data . '.' . $this->b64urlEncode($sig);
    }

    private function b64urlEncode(string $raw): string
    {
        return rtrim(strtr(base64_encode($raw), '+/', '-_'), '=');
    }

    private function b64urlDecode(string $raw): string
    {
        $pad = 4 - (strlen($raw) % 4);
        if ($pad < 4) {
            $raw .= str_repeat('=', $pad);
        }
        return base64_decode(strtr($raw, '-_', '+/'), true) ?: '';
    }
}
