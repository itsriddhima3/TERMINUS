<?php
declare(strict_types=1);

namespace Vault\Cli;

/** Maps operator-facing lifecycle labels to storage column values. */
final class LifecycleIndex
{
    /** @var array<string, string> */
    private const STORAGE_PHASE = [
        'active' => 'live',
        'previous' => 'retired',
    ];

    public static function toStoragePhase(string $filterStatus): string
    {
        return self::STORAGE_PHASE[$filterStatus] ?? $filterStatus;
    }
}
