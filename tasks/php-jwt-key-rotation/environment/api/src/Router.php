<?php
declare(strict_types=1);

namespace Vault\Api;

final class Router
{
    public function __construct(
        private readonly AuthHandler $auth,
        private readonly ResourceHandler $resource,
        private readonly JwksHandler $jwks,
    ) {
    }

    public function dispatch(string $method, string $path): void
    {
        if ($method === 'GET' && $path === '/health') {
            $this->json(200, ['status' => 'ok']);
            return;
        }
        if ($method === 'GET' && $path === '/.well-known/jwks.json') {
            $this->jwks->handle();
            return;
        }
        if ($method === 'POST' && $path === '/auth/login') {
            $this->auth->login();
            return;
        }
        if ($method === 'GET' && $path === '/resource/echo') {
            $this->resource->echo();
            return;
        }
        $this->json(404, ['error' => 'not_found']);
    }

    /** @param array<string, mixed> $body */
    private function json(int $code, array $body): void
    {
        http_response_code($code);
        header('Content-Type: application/json');
        echo json_encode($body, JSON_UNESCAPED_SLASHES);
    }
}
