<?php
declare(strict_types=1);

/** Non-production helper for header inspection only. */
final class TokenParser
{
    public static function headerKid(string $token): string
    {
        $parts = explode('.', $token);
        if (count($parts) < 1) {
            return '';
        }
        $hdr = json_decode(base64_decode(strtr($parts[0], '-_', '+/')), true);
        return (string) ($hdr['kid'] ?? '');
    }
}
