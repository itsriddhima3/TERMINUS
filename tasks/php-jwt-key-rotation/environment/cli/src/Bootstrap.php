<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class Bootstrap
{
    public static function pdo(): PDO
    {
        $db = new PDO('sqlite:/app/var/vault.db');
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $db;
    }

    /** @return array<string, mixed> */
    public static function runtime(): array
    {
        $raw = file_get_contents('/app/platform/runtime.json');
        return json_decode($raw ?: '{}', true, 512, JSON_THROW_ON_ERROR);
    }

    public static function apiBase(): string
    {
        return (string) self::runtime()['api_base'];
    }
}
