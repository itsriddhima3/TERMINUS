<?php
declare(strict_types=1);

require_once __DIR__ . '/src/Bootstrap.php';
require_once __DIR__ . '/src/JwtCrypto.php';
require_once __DIR__ . '/src/HttpSide.php';
require_once __DIR__ . '/src/LifecycleIndex.php';
require_once __DIR__ . '/src/KeyMaterial.php';
require_once __DIR__ . '/src/ClockSkew.php';
require_once __DIR__ . '/src/SigLane.php';
require_once __DIR__ . '/src/EdgeVerifier.php';
require_once __DIR__ . '/src/KeyPromoter.php';
require_once __DIR__ . '/src/RetireCoordinator.php';
require_once __DIR__ . '/src/TokenGate.php';
require_once __DIR__ . '/src/StoreMux.php';
require_once __DIR__ . '/src/RotateHub.php';
require_once __DIR__ . '/src/AuditEmit.php';
require_once __DIR__ . '/src/MapRunner.php';
require_once __DIR__ . '/src/AccessRunner.php';
require_once __DIR__ . '/src/RotateRunner.php';

use Vault\Cli\AccessRunner;
use Vault\Cli\MapRunner;
use Vault\Cli\RotateRunner;

$cmd = $argv[1] ?? '';
match ($cmd) {
    'map' => (new MapRunner())->run(),
    'verify' => (new AccessRunner())->run(),
    'rotate' => (new RotateRunner())->run(),
    default => fwrite(STDERR, "usage: guardctl map|verify|rotate\n"),
};
