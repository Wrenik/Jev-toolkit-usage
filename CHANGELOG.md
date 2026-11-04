# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/). While the major version is 0, minor releases may
change behaviour; they are listed here.

## [Unreleased]

## [0.1.0] - unreleased

The numbers 0.2.0 (Python) and 0.3.0 (mod) were used inside the private monorepo this repository was cut
from; both restart at 0.1.0 here so the first public tag is `v0.1.0`.

### Added
- `jev_core`: `Judge` interface with typed questions (`YesNo`, `Pick`, `Rate`), the TypeSafe Jev adapter, an
  offline `FakeJudge`, an SQLite verdict cache, a JSONL decision log, secret redaction, `JEV_HOME` data
  location, and `ask_together` for sharing one judge call between tools.
- `jev_router`: model/effort policy, local guarded HTTP server, `decide` command.
- `claude-mod/jev-router`: Claude Code mod with `advise`, `auto` and `off` modes and a `/jev` command.
- `python -m jev_router demo`: offline demo of the policy, no key needed.
- `python -m jev_core check` now exits 1 when the chosen judge cannot run, and prints the Python and package
  version; `--version` and `--help` on both entry points.

### Fixed
- A locked, corrupt or read-only cache database no longer fails a judge call (falls back to no caching or
  to an in-memory cache).
- A failing decision-log write (full disk, locked file) no longer loses a verdict that was already paid for.
- `.env` files: `export KEY=value` lines and trailing `# comments` are understood.
- The router server answers (fails open) instead of erroring when the mod sends a malformed `current_model`.
- `python -m jev_router serve` prints a readable message for a busy port, a bad port number or a missing key.
