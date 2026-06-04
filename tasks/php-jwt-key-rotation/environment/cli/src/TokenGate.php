<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

/** Local bearer checks before calling upstream. */
final class TokenGate
{
    public function __construct(private readonly PDO $db)
    {
    }

    /** @return array{ok:bool, reason:string} */
    public function op_verify_a(string $token): array
    {
        unset($this->db);
        return (new SigLane())->authenticate($token);
    }
}
