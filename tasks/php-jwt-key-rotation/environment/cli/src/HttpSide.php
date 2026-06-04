<?php
declare(strict_types=1);

namespace Vault\Cli;

final class HttpSide
{
    public function __construct(private readonly string $base)
    {
    }

    /** @return array{status:int, body:array<string,mixed>|null} */
    public function get(string $path, ?string $bearer = null): array
    {
        return $this->request('GET', $path, null, $bearer);
    }

    /** @param array<string, mixed> $payload */
    public function post(string $path, array $payload): array
    {
        return $this->request('POST', $path, $payload, null);
    }

    /** @param array<string, mixed>|null $payload */
    private function request(string $method, string $path, ?array $payload, ?string $bearer): array
    {
        $ch = curl_init($this->base . $path);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        $headers = ['Accept: application/json'];
        if ($bearer !== null) {
            $headers[] = 'Authorization: Bearer ' . $bearer;
        }
        if ($payload !== null) {
            $body = json_encode($payload, JSON_THROW_ON_ERROR);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
            $headers[] = 'Content-Type: application/json';
        }
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        $raw = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        $decoded = null;
        if (is_string($raw) && $raw !== '') {
            $decoded = json_decode($raw, true);
        }
        return ['status' => $status, 'body' => is_array($decoded) ? $decoded : null];
    }
}
