<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

/** Independent RS256 verification used for reporting, separate from TokenGate. */
final class JwtCrypto
{
    public function __construct(
        private readonly PDO $db,
        private readonly string $issuer,
    ) {
    }

    /** @return array{ok:bool, iss:string, nbf:int, exp:int, kid:string, alg:string} */
    public function verify(string $token): array
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3 || $parts[2] === '') {
            return ['ok' => false, 'iss' => '', 'nbf' => 0, 'exp' => 0, 'kid' => '', 'alg' => ''];
        }
        [$h64, $p64, $s64] = $parts;
        $header = json_decode($this->b64url($h64, true), true) ?? [];
        $payload = json_decode($this->b64url($p64, true), true) ?? [];
        $kid = (string) ($header['kid'] ?? '');
        $alg = (string) ($header['alg'] ?? '');
        $iss = (string) ($payload['iss'] ?? '');
        $nbf = (int) ($payload['nbf'] ?? 0);
        $exp = (int) ($payload['exp'] ?? 0);

        $pub = $this->loadPub($kid);
        if ($pub === null || $alg !== 'RS256') {
            return ['ok' => false, 'iss' => $iss, 'nbf' => $nbf, 'exp' => $exp, 'kid' => $kid, 'alg' => $alg];
        }
        $data = $h64 . '.' . $p64;
        $sig = $this->b64url($s64, true);
        if (openssl_verify($data, $sig, $pub, OPENSSL_ALGO_SHA256) !== 1) {
            return ['ok' => false, 'iss' => $iss, 'nbf' => $nbf, 'exp' => $exp, 'kid' => $kid, 'alg' => $alg];
        }
        $now = time();
        $ok = $iss === $this->issuer && $nbf <= $now && $exp >= $now;
        return ['ok' => $ok, 'iss' => $iss, 'nbf' => $nbf, 'exp' => $exp, 'kid' => $kid, 'alg' => $alg];
    }

    private function loadPub(string $kid): ?string
    {
        if ($kid === '') {
            return null;
        }
        $stmt = $this->db->prepare(
            "SELECT public_pem FROM signing_keys WHERE kid = :kid AND status IN ('active','previous')"
        );
        $stmt->execute([':kid' => $kid]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row ? (string) $row['public_pem'] : null;
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
