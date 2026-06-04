<?php
declare(strict_types=1);

namespace OverlayInspect\Cli;

/**
 * Newline-delimited command parser.
 *
 * Accepts a single trimmed input line and returns a structured form:
 *   ['cmd' => string, 'args' => string[]]
 *
 * Unknown verbs are returned with cmd == 'unknown' so the engine can
 * route an error message to stderr without aborting the play loop.
 */
final class CommandParser {
    public function parse(string $line): array {
        $line = trim($line);
        if ($line === '' || $line[0] === '#') {
            return ['cmd' => 'noop', 'args' => []];
        }
        $tokens = preg_split('/\s+/', $line) ?: [];
        $verb = strtolower((string)array_shift($tokens));
        switch ($verb) {
            case 'mark':
            case 'hint':
            case 'pause':
            case 'quit':
            case 'tick':
            case 'look':
            case 'show':
            case 'noop':
                return ['cmd' => $verb, 'args' => $tokens];
            default:
                return ['cmd' => 'unknown', 'args' => array_merge([$verb], $tokens)];
        }
    }
}
