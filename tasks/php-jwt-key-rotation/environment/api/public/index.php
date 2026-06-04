<?php
declare(strict_types=1);

require_once __DIR__ . '/../src/Router.php';
require_once __DIR__ . '/../src/AuthHandler.php';
require_once __DIR__ . '/../src/ResourceHandler.php';
require_once __DIR__ . '/../src/JwtIssuer.php';
require_once __DIR__ . '/../src/JwksCache.php';
require_once __DIR__ . '/../src/JwksHandler.php';

use Vault\Api\AuthHandler;
use Vault\Api\JwksHandler;
use Vault\Api\JwtIssuer;
use Vault\Api\ResourceHandler;
use Vault\Api\Router;

$cfg = require __DIR__ . '/../config.php';
$db = new PDO('sqlite:' . $cfg['db_path']);
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$issuer = new JwtIssuer($db, $cfg);
$router = new Router(
    new AuthHandler($db, $issuer),
    new ResourceHandler($issuer),
    new JwksHandler($db),
);

$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$router->dispatch($_SERVER['REQUEST_METHOD'] ?? 'GET', $path);
