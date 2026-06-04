<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class RotateRunner
{
    public function run(): void
    {
        $hub = new RotateHub(Bootstrap::pdo());
        $mux = new StoreMux(Bootstrap::pdo());
        $http = new HttpSide(Bootstrap::apiBase());
        $rt = Bootstrap::runtime();
        $db = Bootstrap::pdo();
        $crypto = new JwtCrypto($db, (string) $rt['issuer']);

        $preLogin = $http->post('/auth/login', [
            'username' => (string) $rt['login_user'],
            'password' => (string) $rt['login_password'],
        ]);
        $preToken = (string) ($preLogin['body']['access_token'] ?? '');
        $preKid = $this->headerKid($preToken);
        $preCrypto = $crypto->verify($preToken);

        $result = $hub->phase_c();
        $after = $mux->reconcile_b('active');
        $previous = $mux->reconcile_b('previous');

        $postLogin = $http->post('/auth/login', [
            'username' => (string) $rt['login_user'],
            'password' => (string) $rt['login_password'],
        ]);
        $postToken = (string) ($postLogin['body']['access_token'] ?? '');
        $postKid = $this->headerKid($postToken);
        $postCrypto = $crypto->verify($postToken);

        $gate = new TokenGate($db);
        $preEcho = $http->get('/resource/echo', $preToken);
        $postLocal = $gate->op_verify_a($postToken);
        $postEcho = $http->get('/resource/echo', $postToken);

        $jwks = $http->get('/.well-known/jwks.json');
        $jwksKids = [];
        if (is_array($jwks['body']['keys'] ?? null)) {
            foreach ($jwks['body']['keys'] as $row) {
                $jwksKids[] = (string) ($row['kid'] ?? '');
            }
        }
        sort($jwksKids);

        $prevPrivate = $db->prepare(
            'SELECT private_pem FROM signing_keys WHERE kid = :kid'
        );
        $prevPrivate->execute([':kid' => $result['previous_kid']]);
        $prevPrivVal = $prevPrivate->fetchColumn();

        $auditRows = $mux->count_audit_rows();
        $sequenceOk = $this->auditSequenceOk($db);
        $chainDigest = $this->auditChainDigest($db);

        $payload = [
            'rotated' => count($after) === 1 && ($after[0]['kid'] ?? '') === $result['active_kid'],
            'previous_kid' => $result['previous_kid'],
            'active_kid' => $result['active_kid'],
            'audit_rows' => $auditRows,
            'verify_after_rotate' => $postLocal['ok'] && $postEcho['status'] === 200,
            'pre_rotate_token_valid' => $preEcho['status'] === 200,
            'pre_rotate_kid' => $preKid,
            'post_rotate_kid' => $postKid,
            'previous_private_cleared' => ($prevPrivVal === null || $prevPrivVal === ''),
            'jwks_kids' => $jwksKids,
            'previous_row_count' => count($previous),
            'audit_sequence_ok' => $sequenceOk,
            'audit_chain_digest' => $chainDigest,
            'pre_crypto_ok' => $preCrypto['ok'],
            'post_crypto_ok' => $postCrypto['ok'],
            'signing_key_row_count' => (int) $db->query('SELECT COUNT(*) FROM signing_keys')->fetchColumn(),
        ];
        AuditEmit::write('/app/output/rotation_audit.json', $payload);
    }

    private function headerKid(string $token): string
    {
        $parts = explode('.', $token);
        if (count($parts) < 1) {
            return '';
        }
        $hdr = json_decode($this->b64url($parts[0], true), true) ?? [];
        return (string) ($hdr['kid'] ?? '');
    }

    private function auditSequenceOk(PDO $db): bool
    {
        $rows = $db->query(
            'SELECT event_type, created_at FROM audit_log ORDER BY id ASC'
        )->fetchAll(PDO::FETCH_ASSOC);
        $types = array_column($rows, 'event_type');
        if (!in_array('key_retired', $types, true) || !in_array('key_promoted', $types, true)) {
            return false;
        }
        $retiredAt = null;
        $promotedAt = null;
        foreach ($rows as $row) {
            if ($row['event_type'] === 'key_retired') {
                $retiredAt = $row['created_at'];
            }
            if ($row['event_type'] === 'key_promoted') {
                $promotedAt = $row['created_at'];
            }
        }
        return $retiredAt !== null && $promotedAt !== null && $retiredAt <= $promotedAt;
    }

    private function auditChainDigest(PDO $db): string
    {
        $rows = $db->query(
            'SELECT id, event_type, kid, detail_json, created_at FROM audit_log ORDER BY id ASC'
        )->fetchAll(PDO::FETCH_ASSOC);
        return hash('sha256', json_encode($rows, JSON_THROW_ON_ERROR));
    }

    private function b64url(string $raw, bool $decode = false): string
    {
        if (!$decode) {
            return rtrim(strtr(base64_encode($raw), '+/', '-_'), '=');
        }
        $pad = 4 - (strlen($raw) % 4);
        if ($pad < 4) {
            $raw .= str_repeat('=', $pad);
        }
        return base64_decode(strtr($raw, '-_', '+/'), true) ?: '';
    }
}
