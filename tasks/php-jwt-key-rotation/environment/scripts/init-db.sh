#!/bin/bash
set -euo pipefail

DB=/app/var/vault.db
mkdir -p /app/var /app/keys /app/output

php <<'PHP'
<?php
declare(strict_types=1);
$db = new PDO('sqlite:/app/var/vault.db');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$sql = file_get_contents('/app/data/seed.sql');
foreach (array_filter(array_map('trim', explode(';', $sql))) as $stmt) {
    if ($stmt !== '') {
        $db->exec($stmt);
    }
}
PHP

php <<'PHP'
<?php
declare(strict_types=1);

$db = new PDO('sqlite:/app/var/vault.db');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$pass = password_hash('vault-pass-7', PASSWORD_BCRYPT);
$stmt = $db->prepare('UPDATE users SET pass_hash = :h WHERE username = :u');
$stmt->execute([':h' => $pass, ':u' => 'operator']);

$keyDir = '/app/keys';
if (!is_dir($keyDir)) {
    mkdir($keyDir, 0755, true);
}

$kid = 'key-001';
$bootstrap = '/app/data/bootstrap';
$privPem = file_get_contents("$bootstrap/$kid.pem");
$pubPem = file_get_contents("$bootstrap/$kid.pub.pem");
if ($privPem === false || $pubPem === false) {
    throw new RuntimeException("missing bootstrap key material for $kid");
}

file_put_contents("$keyDir/$kid.pem", $privPem);
file_put_contents("$keyDir/$kid.pub.pem", $pubPem);

$db->exec("DELETE FROM signing_keys");
$ins = $db->prepare(
    'INSERT INTO signing_keys (kid, public_pem, private_pem, status, created_at)
     VALUES (:kid, :pub, :priv, :status, :ts)'
);
$ts = gmdate('c');
$ins->execute([
    ':kid' => $kid,
    ':pub' => $pubPem,
    ':priv' => $privPem,
    ':status' => 'active',
    ':ts' => $ts,
]);
PHP
