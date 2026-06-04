# overlay-inspect

PHP CLI that drives an interactive overlay-inspection workflow against a
seeded challenge pack. The binary lives at `bin/overlay-inspect` and is
expected to be invoked as:

```
php /app/cli/overlay-inspect play <challenge-id>
```

The persistent database is at `/app/state/challenges.db`. The schema is
defined in `persistence/Schema.php` and seeded via
`assets/seed/seed_pack.sql` at image build time
(`assets/seed/bootstrap.sh` orchestrates the bootstrap).

See `docs/architecture.md` for a component-level map and
`docs/cli_help.md` for the supported subcommands and per-play input
grammar. `docs/scoring_profile.md` and `docs/session_states.md` cover
the scoring profile and the state diagram for an in-flight session.

The rendered ASCII previews are produced via the `convert` binary from
ImageMagick — `imaging/MagickRunner.php` is the only place that
shells out, and `docs/grid_geometry.txt` records the rendered grid
dimensions and the assumed cell aspect ratio.
