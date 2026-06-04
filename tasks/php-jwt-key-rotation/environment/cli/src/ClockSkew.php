<?php
declare(strict_types=1);

namespace Vault\Cli;

final class ClockSkew
{
    public static function verifierInstant(): int
    {
        $slack = 90;
        $path = '/app/config/service.toml';
        if (is_readable($path)) {
            $raw = file_get_contents($path) ?: '';
            if (preg_match('/clock_slack_sec\s*=\s*(\d+)/', $raw, $m)) {
                $slack = (int) $m[1];
            }
        }
        return time() + $slack;
    }
}
