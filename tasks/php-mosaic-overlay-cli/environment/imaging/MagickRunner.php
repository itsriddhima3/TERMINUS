<?php
declare(strict_types=1);

namespace OverlayInspect\Imaging;

/**
 * Thin wrapper around the ImageMagick `convert` binary.
 *
 * Reads a source PNG, normalises to greyscale, and emits a row-major
 * intensity buffer. Returned shape: ['source_width' => int, 'source_height' => int, 'pixels' => int[]].
 * Pixel intensities are 0..255 grey.
 */
final class MagickRunner {
    public function fetch(string $absolutePath): array {
        if (!is_file($absolutePath)) {
            throw new \RuntimeException("source image not found: {$absolutePath}");
        }
        $tmp = tempnam(sys_get_temp_dir(), 'oimg_');
        if ($tmp === false) {
            throw new \RuntimeException('failed to allocate temp file');
        }
        try {
            $cmd = sprintf(
                'convert %s -colorspace Gray -depth 8 gray:%s 2>/dev/null',
                escapeshellarg($absolutePath),
                escapeshellarg($tmp)
            );
            $rc = 0;
            $out = [];
            exec($cmd, $out, $rc);
            if ($rc !== 0) {
                throw new \RuntimeException("convert failed: rc={$rc}");
            }
            $identifyCmd = sprintf(
                'identify -format %%w,%%h %s 2>/dev/null',
                escapeshellarg($absolutePath)
            );
            $idOut = [];
            $idRc = 0;
            exec($identifyCmd, $idOut, $idRc);
            if ($idRc !== 0 || empty($idOut)) {
                throw new \RuntimeException("identify failed");
            }
            [$wStr, $hStr] = explode(',', trim($idOut[0]), 2);
            $w = (int)$wStr;
            $h = (int)$hStr;
            $raw = file_get_contents($tmp);
            if ($raw === false) {
                throw new \RuntimeException('failed to read greyscale stream');
            }
            if (strlen($raw) !== $w * $h) {
                throw new \RuntimeException("greyscale stream size {$w}x{$h} != " . strlen($raw));
            }
            $pixels = array_values(unpack('C*', $raw));
            return [
                'source_width' => $w,
                'source_height' => $h,
                'pixels' => $pixels,
            ];
        } finally {
            @unlink($tmp);
        }
    }
}
