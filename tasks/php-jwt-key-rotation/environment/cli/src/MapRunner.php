<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class MapRunner
{
    public function run(): void
    {
        $http = new HttpSide(Bootstrap::apiBase());
        $health = $http->get('/health');
        $db = Bootstrap::pdo();
        $mux = new StoreMux($db);
        $rt = Bootstrap::runtime();

        $endpoints = [
            ['method' => 'GET', 'path' => '/health', 'auth' => false],
            ['method' => 'POST', 'path' => '/auth/login', 'auth' => false],
            ['method' => 'GET', 'path' => '/resource/echo', 'auth' => true],
            ['method' => 'GET', 'path' => '/.well-known/jwks.json', 'auth' => false],
        ];
        usort($endpoints, static fn(array $a, array $b): int => strcmp($a['path'], $b['path']));

        $tables = [
            'signing_keys' => $mux->table_columns('signing_keys'),
            'users' => $mux->table_columns('users'),
            'audit_log' => $mux->table_columns('audit_log'),
        ];
        ksort($tables);

        $activeKid = (string) $db->query(
            "SELECT kid FROM signing_keys WHERE status = 'active' LIMIT 1"
        )->fetchColumn();
        $pubStmt = $db->prepare('SELECT public_pem FROM signing_keys WHERE kid = :kid');
        $pubStmt->execute([':kid' => $activeKid]);
        $pubPem = (string) $pubStmt->fetchColumn();

        $jwks = $http->get('/.well-known/jwks.json');
        $keys = is_array($jwks['body']['keys'] ?? null) ? $jwks['body']['keys'] : [];
        $jwksKids = array_values(array_map(static fn(array $k): string => (string) ($k['kid'] ?? ''), $keys));
        sort($jwksKids);

        $login = $http->post('/auth/login', [
            'username' => (string) $rt['login_user'],
            'password' => (string) $rt['login_password'],
        ]);
        $loginToken = (string) ($login['body']['access_token'] ?? '');
        $lane = (new SigLane())->authenticate($loginToken);

        $histogram = [];
        $rows = $db->query('SELECT status, COUNT(*) AS c FROM signing_keys GROUP BY status')->fetchAll(PDO::FETCH_ASSOC);
        foreach ($rows as $row) {
            $histogram[(string) $row['status']] = (int) $row['c'];
        }
        ksort($histogram);

        $payload = [
            'base_url' => Bootstrap::apiBase(),
            'health_ok' => ($health['status'] === 200),
            'endpoints' => $endpoints,
            'tables' => $tables,
            'active_kid' => $activeKid,
            'jwks_kids' => $jwksKids,
            'login_probe_ok' => ($login['status'] === 200 && $loginToken !== ''),
            'schema_fingerprint' => $this->schemaFingerprint($tables),
            'status_histogram' => $histogram,
            'active_pubkey_digest' => hash('sha256', $pubPem),
            'jwks_bundle_digest' => hash(
                'sha256',
                json_encode($keys, JSON_THROW_ON_ERROR | JSON_PRETTY_PRINT)
            ),
            'login_issuer' => (string) $rt['issuer'],
            'login_crypto_ok' => (bool) $lane['ok'],
        ];
        AuditEmit::write('/app/output/service_map.json', $payload);
    }

    /** @param array<string, list<string>> $tables */
    private function schemaFingerprint(array $tables): string
    {
        $parts = [];
        foreach ($tables as $name => $cols) {
            $parts[] = $name . ':' . implode(',', array_reverse($cols));
        }
        return hash('sha256', implode('|', $parts));
    }
}
