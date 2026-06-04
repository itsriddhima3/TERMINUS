Offline run audit environment (Kotlin).

- `/app/scripts/build-cli.sh` builds `/app/bin/wbaudit` from sources under `/app/cli/`.
- `/app/fixtures/` contains several offline run directories with logs, artifacts, links, and approvals.
- `/app/docs/review/` contains the long security review transcript that the auditor must apply.
- The verifier runs with `UV_OFFLINE=1` (no network resolution during verification).

