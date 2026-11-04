"""python -m jev_router serve [port]               start the local server the Claude Code mod talks to
python -m jev_router decide "<prompt>" [tier]     ask the judge about one prompt and print the decision
python -m jev_router demo                         offline demo: five sample prompts, no key, no network
python -m jev_router --version
"""

from __future__ import annotations

import json
import sys

from jev_core import JudgeError, __version__, default_judge

from .policy import route
from .server import DEFAULT_PORT, serve


def _demo() -> int:
    """Route a few sample prompts with a keyword-driven fake judge, to show what the output looks like."""
    from .demo import run_demo

    return run_demo()


def main(argv: list[str]) -> int:
    cmd = argv[:1]
    if cmd in (["--version"], ["-V"], ["version"]):
        print(f"jev_router {__version__}")
        return 0
    if cmd in (["-h"], ["--help"], ["help"]):
        print(__doc__)
        return 0
    if cmd == ["serve"]:
        try:
            port = int(argv[1]) if len(argv) > 1 else DEFAULT_PORT
        except ValueError:
            print(f"port must be a number, got {argv[1]!r}")
            return 2
        try:
            serve(port)
        except JudgeError as err:
            print(f"cannot start: {err}\nRun `python -m jev_core check` to see what is missing.")
            return 1
        except OSError as err:
            print(f"cannot listen on 127.0.0.1:{port}: {err}\nIs another jev_router already running? Try another port.")
            return 1
        except KeyboardInterrupt:
            return 0
        return 0
    if cmd == ["decide"] and len(argv) > 1:
        try:
            decision, verdict = route(default_judge(tag="router-cli"), argv[1], argv[2] if len(argv) > 2 else None)
        except JudgeError as err:
            print(f"FAILED (would fail open): {err}")
            return 1
        print(json.dumps({**decision.to_dict(), "judge_ms": verdict.latency_ms, "cached": verdict.cached}, indent=2))
        return 0
    if cmd == ["demo"]:
        return _demo()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
