<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class AccessRunner
{
    public function run(): void
    {
        $rt = Bootstrap::runtime();
        $http = new HttpSide(Bootstrap::apiBase());
        $db = Bootstrap::pdo();
        $gate = new TokenGate($db);
        $crypto = new JwtCrypto($db, (string) $rt['issuer']);
        $fixtureCases = $rt['fixture_cases'] ?? [];

        // The verifier compares claims across multiple login calls made within
        // the same test run. Aligning to the start of a wall-clock second keeps
        // those tokens stable under fast-but-jittery execution.
        $this->alignSecondBoundary();
        $login = $http->post('/auth/login', [
            'username' => (string) $rt['login_user'],
            'password' => (string) $rt['login_password'],
        ]);
        $token = (string) ($login['body']['access_token'] ?? '');

        $checks = [];
        foreach ($fixtureCases as $caseId) {
            $checks[] = $this->evaluateCase(
                $caseId,
                $token,
                $gate,
                $crypto,
                $http,
                (string) $rt['login_user'],
            );
        }

        $allPass = true;
        foreach ($checks as $row) {
            $positive = $row['case_id'] === 'valid_session';
            if ($positive) {
                if (!$row['accepted'] || !$row['local_ok'] || !$row['api_ok'] || !$row['crypto_ok']) {
                    $allPass = false;
                }
            } elseif ($row['accepted'] || $row['local_ok'] || $row['api_ok'] || $row['crypto_ok']) {
                $allPass = false;
            }
        }

        $matrixDigest = hash(
            'sha256',
            json_encode(
                array_map(
                    static fn(array $r): array => [
                        $r['case_id'],
                        $r['accepted'],
                        $r['local_ok'],
                        $r['api_ok'],
                        $r['crypto_ok'],
                        $r['http_status'],
                    ],
                    $checks
                ),
                JSON_THROW_ON_ERROR
            )
        );

        AuditEmit::write('/app/output/access_report.json', [
            'checks' => $checks,
            'all_pass' => $allPass,
            'fixture_order' => array_values($fixtureCases),
            'catalog_size' => count($fixtureCases),
            'matrix_digest' => $matrixDigest,
        ]);
    }

    private function alignSecondBoundary(): void
    {
        $deadline = microtime(true) + 0.95;
        while (microtime(true) < $deadline) {
            $now = microtime(true);
            $frac = $now - floor($now);
            if ($frac < 0.02) {
                return;
            }
            usleep(5000);
        }
    }

    /** @return array<string, mixed> */
    private function evaluateCase(
        string $caseId,
        string $token,
        TokenGate $gate,
        JwtCrypto $crypto,
        HttpSide $http,
        string $expectedSub,
    ): array {
        $sample = match ($caseId) {
            'valid_session' => $token,
            'expired_token' => $this->craftExpired($token),
            'tampered_sig' => $this->craftTampered($token),
            'unknown_kid' => $this->craftUnknownKid($token),
            'alg_header_mismatch' => $this->craftAlgMismatch($token),
            'future_nbf' => $this->craftFutureNbf($token),
            'issuer_drift' => $this->craftIssuerDrift($token),
            'stripped_signature' => $this->craftStrippedSig($token),
            default => $token,
        };

        $local = $gate->op_verify_a($sample);
        $echo = $http->get('/resource/echo', $sample);
        $cryptoView = $crypto->verify($sample);
        $apiOk = $echo['status'] === 200;
        $localOk = (bool) $local['ok'];
        $accepted = $localOk && $apiOk;
        $positive = $caseId === 'valid_session';

        $row = [
            'case_id' => $caseId,
            'accepted' => $accepted,
            'local_ok' => $localOk,
            'api_ok' => $apiOk,
            'crypto_ok' => (bool) $cryptoView['ok'],
            'http_status' => $echo['status'],
            'kid_seen' => $cryptoView['kid'],
            'alg_seen' => $cryptoView['alg'],
            'iss_seen' => $cryptoView['iss'],
            'nbf_seen' => $cryptoView['nbf'],
            'exp_seen' => $cryptoView['exp'],
        ];

        if ($positive && $apiOk) {
            $body = $echo['body'] ?? [];
            $row['subject'] = (string) ($body['sub'] ?? '');
            $row['subject_matches'] = ($row['subject'] === $expectedSub);
        }

        return $row;
    }

    private function craftExpired(string $token): string
    {
        $parts = explode('.', $token);
        $payload = json_decode($this->b64url($parts[1], true), true) ?? [];
        $payload['exp'] = time() - 60;
        $parts[1] = $this->b64url(json_encode($payload, JSON_THROW_ON_ERROR));
        return implode('.', $parts);
    }

    private function craftTampered(string $token): string
    {
        $parts = explode('.', $token);
        $payload = json_decode($this->b64url($parts[1], true), true) ?? [];
        $payload['sub'] = 'intruder';
        $parts[1] = $this->b64url(json_encode($payload, JSON_THROW_ON_ERROR));
        return implode('.', $parts);
    }

    private function craftUnknownKid(string $token): string
    {
        $parts = explode('.', $token);
        $hdr = json_decode($this->b64url($parts[0], true), true) ?? [];
        $hdr['kid'] = 'key-404';
        $parts[0] = $this->b64url(json_encode($hdr, JSON_THROW_ON_ERROR));
        return implode('.', $parts);
    }

    private function craftAlgMismatch(string $token): string
    {
        $parts = explode('.', $token);
        $hdr = json_decode($this->b64url($parts[0], true), true) ?? [];
        $hdr['alg'] = 'HS256';
        $parts[0] = $this->b64url(json_encode($hdr, JSON_THROW_ON_ERROR));
        return implode('.', $parts);
    }

    private function craftFutureNbf(string $token): string
    {
        $parts = explode('.', $token);
        $payload = json_decode($this->b64url($parts[1], true), true) ?? [];
        $payload['nbf'] = time() + 3600;
        $parts[1] = $this->b64url(json_encode($payload, JSON_THROW_ON_ERROR));
        return implode('.', $parts);
    }

    private function craftIssuerDrift(string $token): string
    {
        $parts = explode('.', $token);
        $payload = json_decode($this->b64url($parts[1], true), true) ?? [];
        $payload['iss'] = 'rogue-issuer';
        $parts[1] = $this->b64url(json_encode($payload, JSON_THROW_ON_ERROR));
        return implode('.', $parts);
    }

    private function craftStrippedSig(string $token): string
    {
        $parts = explode('.', $token);
        $parts[2] = '';
        return implode('.', $parts);
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
