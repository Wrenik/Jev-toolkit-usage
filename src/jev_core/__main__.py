"""python -m jev_core check      setup report, no network (exit 1 if the chosen judge cannot run)
python -m jev_core smoke      one real judge call (a fraction of a cent with Jev)
python -m jev_core --version"""

from __future__ import annotations

import platform
import sys

from . import __version__
from .config import default_judge, find_env_file, home, load_env, var_path
from .judge import JudgeError
from .types import Pick, Question, Rate, YesNo

SMOKE_STATE = "Rename the variable `cnt` to `count` in utils.py."
SMOKE_QUESTIONS: dict[str, Question] = {
    "mechanical": YesNo("Is this a small mechanical code edit with no design decisions?"),
    "risk": Pick("What is the risk of this request?", {"none": None, "low": None, "high": "could delete data or break things"}),
    "complexity": Rate("How complex is this task?", ["trivial", "small", "medium", "large", "very large"]),
}


def main(argv: list[str]) -> int:
    command = argv[0] if argv else "check"
    if command in ("--version", "-V", "version"):
        print(f"jev_core {__version__}")
        return 0
    if command in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if command == "check":
        env = load_env()
        print(f"jev_core {__version__}, Python {platform.python_version()} on {platform.system()}")
        print(f".env file: {find_env_file() or 'not found'}")
        print(f"data home (JEV_HOME): {home()}  logs and databases: {var_path()}")
        print(f"judge: {env.get('JEV_JUDGE', 'jev')}  model: {env.get('JEV_MODEL', '(default)')}")
        # Never print the key itself.
        kind = env.get("JEV_JUDGE", "jev")
        has_key = bool(env.get("TYPESAFE_API_KEY"))
        print(f"TYPESAFE_API_KEY: {'set' if has_key else 'MISSING'}")
        if kind == "jev" and not has_key:
            print(f"-> No key: put TYPESAFE_API_KEY=... in {find_env_file() or home() / '.env'} (copy .env.example), "
                  "or set JEV_JUDGE=fake to run offline.")
            return 1
        if kind not in ("jev", "fake"):
            print(f"-> Unknown JEV_JUDGE {kind!r}; use 'jev' or 'fake'.")
            return 1
        print("OK" + (" (offline fake judge)" if kind == "fake" else ""))
        return 0
    if command == "smoke":
        try:
            verdict = default_judge(tag="smoke").ask(SMOKE_STATE, SMOKE_QUESTIONS)
        except JudgeError as err:
            print(f"FAILED: {err}")
            return 1
        print(f"model={verdict.model} tokens={verdict.input_tokens} cost=${verdict.cost_usd:.8f} "
              f"latency={verdict.latency_ms}ms cached={verdict.cached}")
        for name, answer in verdict.answers.items():
            print(f"  {name}: {answer}")
        return 0
    print(f"unknown command {command!r}")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
