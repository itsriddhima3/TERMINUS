<?php
declare(strict_types=1);

namespace Vault\Api;

final class ResourceHandler
{
    public function __construct(private readonly JwtIssuer $issuer)
    {
    }

    public function echo(): void
    {
        $hdr = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
        if (!str_starts_with($hdr, 'Bearer ')) {
            http_response_code(401);
            echo json_encode(['error' => 'missing_bearer']);
            return;
        }
        $token = substr($hdr, 7);
        try {
            $payload = $this->issuer->verify($token);
        } catch (\Throwable) {
            http_response_code(401);
            echo json_encode(['error' => 'invalid_token']);
            return;
        }
        http_response_code(200);
        header('Content-Type: application/json');
        echo json_encode([
            'message' => 'echo',
            'sub' => (string) ($payload['sub'] ?? ''),
        ], JSON_UNESCAPED_SLASHES);
    }
}
