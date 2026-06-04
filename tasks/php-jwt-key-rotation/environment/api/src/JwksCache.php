<?php
declare(strict_types=1);

namespace Vault\Api;

final class JwksCache
{
    /** @var list<array<string, mixed>>|null */
    private static ?array $keys = null;

    /** @param list<array<string, mixed>> $keys */
    public static function remember(array $keys): void
    {
        self::$keys = $keys;
    }

    /** @return list<array<string, mixed>>|null */
    public static function get(): ?array
    {
        return self::$keys;
    }

    public static function forget(): void
    {
        self::$keys = null;
    }
}
