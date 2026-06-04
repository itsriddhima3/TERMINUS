<?php
declare(strict_types=1);

namespace OverlayInspect;

require_once __DIR__ . '/../persistence/Connection.php';
require_once __DIR__ . '/../persistence/Schema.php';
require_once __DIR__ . '/../persistence/Tally.php';
require_once __DIR__ . '/../persistence/Sink.php';
require_once __DIR__ . '/../persistence/Audit.php';
require_once __DIR__ . '/../imaging/MagickRunner.php';
require_once __DIR__ . '/../imaging/AsciiTransformer.php';
require_once __DIR__ . '/../imaging/Coord/AffineWarp.php';
require_once __DIR__ . '/../imaging/Coord/Translate.php';
require_once __DIR__ . '/../imaging/Coord/Polar.php';
require_once __DIR__ . '/../imaging/Pipeline/Stretch.php';
require_once __DIR__ . '/../imaging/Pipeline/Crop.php';
require_once __DIR__ . '/../imaging/Pipeline/Quantize.php';
require_once __DIR__ . '/../game/PackLoader.php';
require_once __DIR__ . '/../game/Overlap.php';
require_once __DIR__ . '/../lifecycle/Lifecycle.php';
require_once __DIR__ . '/../lifecycle/Replay.php';
require_once __DIR__ . '/../game/Throttle.php';
require_once __DIR__ . '/../game/Gate.php';
require_once __DIR__ . '/../game/Reckon.php';
require_once __DIR__ . '/../game/Wager.php';
require_once __DIR__ . '/CommandParser.php';
require_once __DIR__ . '/OutputRenderer.php';
require_once __DIR__ . '/Loop.php';

use OverlayInspect\Cli\Loop;
use OverlayInspect\Cli\OutputRenderer;
use OverlayInspect\Persistence\Connection;
use OverlayInspect\Persistence\Schema;
use OverlayInspect\Persistence\Tally;
use OverlayInspect\Persistence\Sink;
use OverlayInspect\Persistence\Audit;
use OverlayInspect\Imaging\MagickRunner;
use OverlayInspect\Imaging\AsciiTransformer;
use OverlayInspect\Imaging\Coord\AffineWarp;
use OverlayInspect\Imaging\Pipeline\Stretch;
use OverlayInspect\Game\PackLoader;
use OverlayInspect\Game\Overlap;
use OverlayInspect\Game\Lifecycle;
use OverlayInspect\Game\Throttle;
use OverlayInspect\Game\Reckon;

final class Bootstrap {
    public static function main(array $argv): int {
        $configPath = '/app/config/runtime.ini';
        if (!is_file($configPath)) {
            fwrite(STDERR, "missing runtime config at {$configPath}\n");
            return 2;
        }
        $config = parse_ini_file($configPath, true, INI_SCANNER_TYPED);
        $gridConfig = json_decode((string)file_get_contents('/app/config/grid_dimensions.json'), true, 512, JSON_THROW_ON_ERROR);
        $scoringConfig = json_decode((string)file_get_contents('/app/config/scoring_profile.json'), true, 512, JSON_THROW_ON_ERROR);

        $pdo = Connection::open((string)$config['paths']['db_path']);
        Schema::ensure($pdo);

        $tally = new Tally($pdo);
        $sink = new Sink($pdo);
        $audit = new Audit($pdo);
        $magick = new MagickRunner();
        $ascii = new AsciiTransformer((string)$config['render']['glyph_palette']);
        $cellAspect = (float)$gridConfig['cell_aspect_ratio_w_over_h'];
        $affine = new AffineWarp($cellAspect);
        $stretch = new Stretch($cellAspect);
        $packLoader = new PackLoader($pdo, '/app');
        $overlap = new Overlap($affine);
        $lifecycle = new Lifecycle($pdo, $tally, $audit);
        $throttle = new Throttle();
        $reckon = new Reckon(
            (int)$scoringConfig['decay_per_second'],
            (int)$scoringConfig['rounding_step'],
        );

        $renderer = new OutputRenderer();
        $loop = new Loop(
            $pdo,
            $packLoader,
            $lifecycle,
            $stretch,
            $magick,
            $ascii,
            $overlap,
            $throttle,
            $reckon,
            $tally,
            $sink,
            $audit,
            $renderer,
            $gridConfig,
            $scoringConfig,
        );

        $cmd = $argv[1] ?? '';
        $rest = array_slice($argv, 2);
        switch ($cmd) {
            case 'play':
                return $loop->play($rest);
            case 'list':
                return $loop->listPacks();
            case 'describe':
                if (!isset($rest[0])) {
                    fwrite(STDERR, "describe requires a challenge id\n");
                    return 2;
                }
                return $loop->describe($rest[0]);
            case 'overlay-help':
                return $loop->overlayHelp();
            case 'reset':
                return $loop->resetDb();
            case '':
            case '-h':
            case '--help':
                $renderer->renderHelp();
                return 0;
            default:
                fwrite(STDERR, "unknown subcommand: {$cmd}\n");
                return 2;
        }
    }
}
