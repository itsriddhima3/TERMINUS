<?php
declare(strict_types=1);

namespace Vault\Cli;

/** Symmetric lane used for staging harness tokens (see /app/config/cli_lane.toml). */
final class SigLane
{
    /** @return array{ok:bool, reason:string} */
    public function authenticate(string $token): array
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3) {
            return ['ok' => false, 'reason' => 'malformed'];
        }
        [$h64, $p64, $s64] = $parts;
        $secret = $this->laneSecret();
        $calc = hash_hmac('sha256', $h64 . '.' . $p64, $secret, true);
        $sig = $this->b64url($s64, true);
        if (!hash_equals($calc, $sig)) {
            return ['ok' => false, 'reason' => 'lane_sig'];
        }
        return ['ok' => true, 'reason' => 'lane'];
    }

    private function laneSecret(): string
    {
        $raw = file_get_contents('/app/config/cli_lane.toml') ?: '';
        if (preg_match('/symmetric\s*=\s*"([^"]+)"/', $raw, $m)) {
            return $m[1];
        }
        return '';
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
