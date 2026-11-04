"""Where the toolkit keeps its data, plus settings loading and the default judge stack.

Data location (all tools use these functions, never a literal ``Path("var")``):

* ``JEV_HOME`` (environment variable), default ``~/.jev-toolkit``, holds one ``.env`` (the TypeSafe key,
  shared by every tool) and ``var/`` (logs, caches, databases, state).
* Development compatibility: when ``JEV_HOME`` is NOT set and the current directory is a toolkit checkout
  (it has ``src/jev_core``) or already has a ``var/`` folder with toolkit files in it, that ``var/`` is used, as
  before the split. A nearer ``.env`` (current directory or any parent) also still wins over ``JEV_HOME/.env``.
  An explicitly set ``JEV_HOME`` always wins for ``var/``, so a server started by a mod from some unrelated
  project folder does not write into that project.
"""

from __future__ import annotations

import os
from pathlib import Path

from .cache import CachingJudge
from .judge import Judge, JudgeConfigError
from .log import LoggingJudge

# Files and folders the tools create in var/. Their presence marks a var/ folder as ours.
_VAR_MARKERS = ("judge-cache.sqlite", "judge-log.jsonl", "router-log.jsonl", "context-advice.jsonl", "log")


def home() -> Path:
    """The data root: ``JEV_HOME`` if set, else ``~/.jev-toolkit``. Not created here."""
    explicit = os.environ.get("JEV_HOME")
    return Path(explicit).expanduser() if explicit else Path.home() / ".jev-toolkit"


def _dev_var(cwd: Path) -> Path | None:
    var = cwd / "var"
    if (cwd / "src" / "jev_core").is_dir() or (var.is_dir() and any((var / m).exists() for m in _VAR_MARKERS)):
        return var
    return None


def var_path() -> Path:
    """Folder for logs, caches and databases (created on first use by the tool that writes there)."""
    if not os.environ.get("JEV_HOME"):
        dev = _dev_var(Path.cwd().resolve())
        if dev is not None:
            return dev
    return home() / "var"


def env_files(start: Path | None = None) -> list[Path]:
    """Existing settings files, highest priority first: JEV_TOOLKIT_ENV alone; else the nearest .env from
    `start` (default cwd) upward, then ``JEV_HOME/.env`` as the shared fallback."""
    explicit = os.environ.get("JEV_TOOLKIT_ENV")
    if explicit:
        return [Path(explicit)]
    found: list[Path] = []
    here = (start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        candidate = folder / ".env"
        if candidate.is_file():
            found.append(candidate)
            break
    shared = home() / ".env"
    if shared.is_file() and shared.resolve() not in [f.resolve() for f in found]:
        found.append(shared)
    return found


def find_env_file(start: Path | None = None) -> Path | None:
    """The settings file that takes priority, or None."""
    files = env_files(start)
    return files[0] if files else None


def _parse(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):  # `export KEY=value` is a common shell-style .env line
            line = line[len("export "):].lstrip()
        key, _, value = line.partition("=")
        value = value.strip()
        if value[:1] in ("'", '"') and value.count(value[0]) >= 2:
            value = value[1 : value.index(value[0], 1)]  # quoted: ignore anything after the closing quote
        else:
            value = value.split(" #", 1)[0].strip()  # unquoted: a trailing ` # comment` is not part of the value
        values[key.strip()] = value
    return values


def load_env(path: Path | None = None) -> dict[str, str]:
    """Minimal KEY=VALUE parser. Real environment variables win over files; a nearer file wins over
    ``JEV_HOME/.env``. An explicit `path` is read alone."""
    values: dict[str, str] = {}
    files = [path] if path else env_files()
    for file in reversed(files):  # lowest priority first, so higher ones overwrite
        if file and file.is_file():
            values.update(_parse(file))
    for key in ("TYPESAFE_API_KEY", "JEV_MODEL", "JEV_JUDGE"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def default_judge(
    var_dir: str | Path | None = None, tag: str | None = None, timeout: float | None = None, max_retries: int | None = None
) -> Judge:
    """Logging(Caching(real judge)), chosen by JEV_JUDGE: "jev" (default) or "fake".

    `var_dir` defaults to ``var_path()``. `timeout` (seconds per attempt) and `max_retries` override the
    Jev adapter defaults (10 s, 1 retry, i.e. up to ~20 s): interactive callers such as the router want a
    short bound.
    """
    env = load_env()
    kind = env.get("JEV_JUDGE", "jev")
    if kind == "fake":
        from .fake import FakeJudge

        inner: Judge = FakeJudge()
    elif kind == "jev":
        key = env.get("TYPESAFE_API_KEY")
        if not key:
            raise JudgeConfigError("TYPESAFE_API_KEY is not set (put it in JEV_HOME/.env or ./.env, see .env.example)")
        from .jev import DEFAULT_MODEL, JevJudge

        extra: dict = {}
        if timeout is not None:
            extra["timeout"] = timeout
        if max_retries is not None:
            extra["max_retries"] = max_retries
        inner = JevJudge(api_key=key, model=env.get("JEV_MODEL") or DEFAULT_MODEL, **extra)
    else:
        raise JudgeConfigError(f"unknown JEV_JUDGE {kind!r}; use 'jev' or 'fake'")
    var = Path(var_dir) if var_dir is not None else var_path()
    return LoggingJudge(CachingJudge(inner, var / "judge-cache.sqlite"), var / "judge-log.jsonl", tag=tag)
