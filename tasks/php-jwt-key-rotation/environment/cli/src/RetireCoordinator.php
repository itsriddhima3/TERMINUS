<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class RetireCoordinator
{
    public static function markRetired(PDO $db, string $kid, string $successorKid): void
    {
        unset($db, $kid, $successorKid);
    }
}
