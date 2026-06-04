<?php
declare(strict_types=1);

namespace Vault\Api;

use PDO;

final class JwksHandler
{
    public function __construct(private readonly PDO $db)
    {
    }

    public function handle(): void
    {
        $cached = JwksCache::get();
        if ($cached !== null) {
            http_response_code(200);
            header('Content-Type: application/json');
            echo json_encode(['keys' => $cached], JSON_UNESCAPED_SLASHES);
            return;
        }

        $stmt = $this->db->query(
            "SELECT kid, public_pem FROM signing_keys WHERE status IN ('active','previous') ORDER BY kid"
        );
        $keys = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $keys[] = $this->jwkFromPem((string) $row['kid'], (string) $row['public_pem']);
        }
        JwksCache::remember($keys);
        http_response_code(200);
        header('Content-Type: application/json');
        echo json_encode(['keys' => $keys], JSON_UNESCAPED_SLASHES);
    }

    /** @return array<string, mixed> */
    private function jwkFromPem(string $kid, string $pem): array
    {
        $res = openssl_pkey_get_public($pem);
        $details = openssl_pkey_get_details($res);
        $n = $this->b64urlEncode($details['rsa']['n']);
        $e = $this->b64urlEncode($details['rsa']['e']);
        return [
            'kty' => 'RSA',
            'kid' => $kid,
            'alg' => 'RS256',
            'use' => 'sig',
            'n' => $n,
            'e' => $e,
        ];
    }

    private function b64urlEncode(string $raw): string
    {
        return rtrim(strtr(base64_encode($raw), '+/', '-_'), '=');
    }
}
