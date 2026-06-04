<?php
declare(strict_types=1);

namespace Vault\Api;

use PDO;

final class AuthHandler
{
    public function __construct(
        private readonly PDO $db,
        private readonly JwtIssuer $issuer,
    ) {
    }

    public function login(): void
    {
        $body = json_decode(file_get_contents('php://input') ?: '{}', true) ?? [];
        $user = (string) ($body['username'] ?? '');
        $pass = (string) ($body['password'] ?? '');
        $stmt = $this->db->prepare('SELECT pass_hash FROM users WHERE username = :u LIMIT 1');
        $stmt->execute([':u' => $user]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$row || !password_verify($pass, (string) $row['pass_hash'])) {
            http_response_code(401);
            echo json_encode(['error' => 'invalid_credentials']);
            return;
        }
        $token = $this->issuer->issue($user);
        http_response_code(200);
        header('Content-Type: application/json');
        echo json_encode([
            'access_token' => $token,
            'token_type' => 'Bearer',
            'expires_in' => 3600,
        ], JSON_UNESCAPED_SLASHES);
    }
}
