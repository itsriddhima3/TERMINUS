<?php
declare(strict_types=1);

namespace Vault\Cli;

use PDO;

final class RotateHub
{
    public function __construct(private readonly PDO $db)
    {
    }

    /** @return array{previous_kid:string, active_kid:string} */
    public function phase_c(): array
    {
        $active = $this->db->query(
            "SELECT kid FROM signing_keys WHERE status = 'active' LIMIT 1"
        )->fetch(PDO::FETCH_ASSOC);
        $prevKid = $active ? (string) $active['kid'] : '';
        $newKid = 'key-002';

        $priv = openssl_pkey_new([
            'private_key_bits' => 2048,
            'private_key_type' => OPENSSL_KEYTYPE_RSA,
        ]);
        openssl_pkey_export($priv, $privPem);
        $details = openssl_pkey_get_details($priv);
        $pubPem = $details['key'];
        $ts = gmdate('c');

        KeyPromoter::insertActive($this->db, $newKid, $pubPem, $privPem, $ts);
        RetireCoordinator::markRetired($this->db, $prevKid, $newKid);
        $this->append_audit('key_promoted', $newKid, ['from' => $prevKid]);
        return ['previous_kid' => $prevKid, 'active_kid' => $newKid];
    }

    /** @param array<string, mixed> $detail */
    private function append_audit(string $event, string $kid, array $detail): void
    {
        $stmt = $this->db->prepare(
            'INSERT INTO audit_log (event_type, kid, detail_json, created_at) VALUES (:e, :k, :d, :t)'
        );
        $stmt->execute([
            ':e' => $event,
            ':k' => $kid,
            ':d' => json_encode($detail, JSON_THROW_ON_ERROR),
            ':t' => gmdate('c'),
        ]);
    }
}
