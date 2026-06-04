<?php
declare(strict_types=1);

namespace Vault\Cli;

final class AuditEmit
{
    public static function write(string $path, array $payload): void
    {
        $dir = dirname($path);
        if (!is_dir($dir)) {
            mkdir($dir, 0755, true);
        }
        file_put_contents(
            $path,
            json_encode($payload, JSON_UNESCAPED_SLASHES) . "\n",
            LOCK_EX
        );
    }
}
