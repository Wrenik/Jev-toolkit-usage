# Jev-toolkit-usage

[![tests](https://github.com/Wrenik/Jev-toolkit-usage/actions/workflows/tests.yml/badge.svg)](https://github.com/Wrenik/Jev-toolkit-usage/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![status](https://img.shields.io/badge/status-alpha-orange)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

(The badges start working once the repository is public.)

Small tools that put a **judgement model** next to a generative LLM. The LLM writes; the judgement model answers typed questions (yes/no, pick one, rate on a scale) with probabilities; ordinary code acts on those answers. The first judge supported is [TypeSafe Jev](https://docs.typesafe.ai).

This repository is the **base** of a family of Jev tools: the judge layer (`jev_core`) and the first tool built on it, a model/effort router for Claude Code (`jev_router` + the `jev-router` mod). The other tools live in sibling repositories and depend on this one (see [the family](#the-jev-toolkit-family)).

## Status and limits

| Part | State |
|---|---|
| `jev_core`: judge interface, Jev adapter, fake judge, cache, decision log, redaction | **Working.** Unit-tested offline; live calls to Jev work (the router makes them on every prompt), but there is no automated test against the live API. |
| Model/effort router for Claude Code (`jev_router` + `claude-mod/jev-router`) | **Working in Claude Code desktop**, still being tuned. Asks Jev about each prompt (~0.3 s), switches model/effort in `auto` mode or only suggests in `advise` mode. It only steps *down* a tier when the context is small or the cache is cold, because a model switch throws away the prompt cache. It never switches away from models it doesn't manage (Fable, opusplan, 1M variants), never drops a prompt sent mid-turn or holding `@mentions`, and redacts likely secrets before a prompt goes to the judge. Thresholds are first guesses. See [the bug report](docs/BUG_REPORT_2026-10-30.md). |
| Data location (`JEV_HOME`) | New in this split; unit-tested, not yet used by anyone but the author. |
| Design and roadmap ([DESIGN.md](docs/DESIGN.md), [ROADMAP.md](docs/ROADMAP.md)) | Written before the repositories were split; they describe the whole family. |

## Install

Requires Python 3.11+.

```bash
pip install "git+https://github.com/Wrenik/Jev-toolkit-usage.git"     # once the repository is public
# or, from a clone:
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"                          # Windows; use .venv/bin/python elsewhere
```

### Install all six tools at once

`scripts/install_all.ps1` (Windows) and `scripts/install_all.sh` (macOS/Linux) clone the six repositories, install them in dependency order into one venv, create `JEV_HOME` and its `.env` without asking anything, and run `python -m jev_core check`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_all.ps1 -Dir ..\jev-all      # add -Offline to try without a key
```

```bash
scripts/install_all.sh --dir ../jev-all                                                 # add --offline to try without a key
```

Details, options, installing from local clones before the repositories are public, and the by-hand steps: [docs/INSTALL_ALL.md](docs/INSTALL_ALL.md).

### Where your data and key live (`JEV_HOME`)

All tools keep their data in one place: the folder named by the environment variable `JEV_HOME`, default `~/.jev-toolkit`:

```
~/.jev-toolkit/.env     your TYPESAFE_API_KEY (one key for every Jev tool); copy .env.example there
~/.jev-toolkit/var/     logs, caches, databases and state of all tools
```

For development, a `.env` in the current directory (or a parent) still wins over `JEV_HOME/.env`, and inside a clone of this repository (or any folder whose `var/` already holds toolkit files) that `var/` is used, as before. An explicitly set `JEV_HOME` always wins for `var/`. Delete the folder to delete everything the tools stored.

```bash
python -m jev_core check      # shows whether the key is found and where data goes (never prints the key)
python -m jev_core smoke      # one real Jev call, a fraction of a cent
python -m pytest              # offline tests, no key needed
```

No key? Set `JEV_JUDGE=fake` and everything runs offline with a neutral fake judge (`check` then reports `OK (offline fake judge)`; `python -m jev_router demo` needs no key at all).

### Using a different judge

`JEV_JUDGE` picks the judge: `jev` (default), `fake`, `some.module:factory`, or the name of an entry point in the `jev_core.judges` group. The factory takes no arguments, reads its own settings from the environment and returns an object with `name`, `model` and `ask(state, questions) -> Verdict` (see `jev_core.judge.Judge`). Raise `JudgeUnavailable` for transient failures, `JudgeConfigError` for permanent ones. Caching and logging are wrapped around it automatically. Stub for a local model (docs only, no dependency added):

```python
# my_local_judge.py   ->   JEV_JUDGE=my_local_judge:make
import os
from jev_core.judge import JudgeUnavailable
from jev_core.types import YesNo, YesNoAnswer, Verdict


class LocalJudge:
    name, model = "local", os.environ.get("LOCAL_MODEL", "my-model")

    def ask(self, state, questions):
        # call your local/EU model here; map its output to one Answer per question
        answers = {k: YesNoAnswer(p_yes=0.5) for k, q in questions.items() if isinstance(q, YesNo)}
        return Verdict(answers=answers, model=self.model, input_tokens=0, latency_ms=0)


def make():
    return LocalJudge()
```

Or register it for installs: `[project.entry-points."jev_core.judges"]` `local = "my_local_judge:make"`, then `JEV_JUDGE=local`. Background and sources: [docs/PRIOR_ART.md](docs/PRIOR_ART.md).

## Quick try (offline, no key)

Works the same on Windows, macOS and Linux; you need Python 3.11 or newer and git.

```bash
git clone https://github.com/Wrenik/Jev-toolkit-usage.git     # or use your local copy
cd Jev-toolkit-usage
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"                  # Windows; macOS/Linux: .venv/bin/python
.venv/Scripts/python -m jev_router demo                          # offline demo
.venv/Scripts/python -m pytest                                   # offline tests
```

The demo uses canned judge answers (no network) and prints what the router would choose for five sample prompts:

```
> Rename the variable cnt to count in utils.py.
  -> light    haiku / effort low   (small mechanical task)
> yes, go ahead
  -> standard sonnet / effort medium   (ordinary task)
> Add a --verbose flag to the CLI and document it.
  -> standard sonnet / effort high   (ordinary task)
> Find why the nightly sync loses rows only on Mondays; the cause is unknown.
  -> heavy    opus / effort high   (complex coding work: Opus rather than staying on Sonnet)
> Delete all rows older than a year from the production database.
  -> heavy    opus / effort high   (high risk)
```

To use the real judge, put your TypeSafe key in `~/.jev-toolkit/.env` (copy `.env.example`) and run
`python -m jev_core check` (setup report, no network, never prints the key) then `python -m jev_core smoke` (one real call).
`JEV_JUDGE=fake` makes every command run offline with a neutral fake judge.

**Troubleshooting.** `python -m jev_core check` is the first thing to run; it says what is missing. If `pip` hangs while
downloading, your network probably has a broken IPv6 route: retry with `pip install --timeout 30 --retries 5 ...`
or switch IPv6 off for the install. If the mod says the router is unreachable, start the server by hand
(`python -m jev_router serve`) and read its message; "cannot listen" means another copy already runs on port 8765.

## About this project

This is a personal learning project, built by an IT student (security now, data science next) to find out how a *judgement model* behaves when you put it next to a generative LLM. It is an experiment: I wanted to work out for myself where a model that returns typed answers with probabilities is useful, what breaks, and what it costs. Much of the code was written together with Claude Code, and the [bug report](docs/BUG_REPORT_2026-10-30.md) shows the mistakes found along the way, not only the result.

**None of the ideas here are original.** Model routing, typed outputs and LLM judges all exist already; see [Prior art](#prior-art). Mature tools such as RouteLLM, LiteLLM and Instructor are better choices if you need something reliable. What this repo offers is a small, readable, tested experiment with a swappable judge, and honest notes on what worked.

## Why a judgement model

A generative LLM is a poor referee of its own work. A model that returns *typed answers with probabilities* gives code something it can compare against a threshold, log, and audit. Jev is built for exactly that, and it is cheap: about $0.042 per million input tokens, output free (October 2026 price).

## Built for Claude Code on a subscription

The tools are meant to work with a Claude Pro/Max **subscription inside Claude Code**, not with pay-per-token API keys. They hook into Claude Code's own extension points (mods, hooks, MCP tools). The judge side is model-independent; the generative side is whatever Claude Code session (or later, local LLM) you already run.

## Install the Claude Code mod (`jev-router`)

The mod needs Claude Code with mod support (a recent version; check with `claude plugin --help`) and `python` on your PATH with this package installed (`pip install` as above, into the Python that `python` runs; set `JEV_PYTHON` or the mod's `python` option to use another interpreter, e.g. `python3`). The mod starts `python -m jev_router serve` itself; it needs no path to a checkout.

```
/plugin marketplace add Wrenik/Jev-toolkit-usage
/plugin install jev-router --marketplace Wrenik/Jev-toolkit-usage
```

or load it straight from a clone by adding `claude-mod/jev-router` to `CLAUDE_CODE_PLUGIN_DIRS`. The mod starts in `advise` mode (it only suggests); `/jev` shows its state and lets you switch to `auto` or `off`. Mod tests: `claude plugin test claude-mod/jev-router`.

## Using `jev_core`

```python
from jev_core import Pick, Rate, YesNo, default_judge

judge = default_judge(tag="example")  # Jev, wrapped in a cache and a JSONL decision log
verdict = judge.ask(
    "Rename the variable cnt to count in utils.py.",
    {
        "mechanical": YesNo("Is this a small mechanical edit with no design decisions?"),
        "risk": Pick("What is the risk?", {"none": None, "low": None, "high": "could delete data"}),
        "complexity": Rate("How complex is this?", ["trivial", "small", "medium", "large"]),
    },
)
verdict["mechanical"].p_yes  # probability of "yes", 0..1
verdict["risk"].probabilities  # {"none": ..., "low": ..., "high": ...}
verdict["complexity"].level  # most probable level
verdict.cost_usd, verdict.cached
```

Ask several questions in one call: you pay for the state's tokens once. Errors come in two kinds so each tool can choose how to fail: `JudgeUnavailable` (network, timeout, rate limit; try later) and `JudgeConfigError` (bad key or request; fix the setup). Routers should fail **open** (do nothing); security tools should fail **closed** (block).

## Layout

```
src/jev_core/    types.py judge.py jev.py (the only module that talks to TypeSafe) fake.py cache.py log.py
                 redact.py config.py (settings and data location) localserver.py (guarded local HTTP base) joint.py
src/jev_router/  the router policy and its local server
claude-mod/jev-router/   the Claude Code mod (TypeScript)
scripts/         install_all.ps1, install_all.sh (all six tools in one venv)
docs/            INSTALL_ALL.md, DESIGN.md, ROADMAP.md, BUG_REPORT_2026-10-30.md, RELEASE_NOTES_v0.1.0.md
CHANGELOG.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, CITATION.cff
tests/           offline tests
```

## Known limits

- Only text questions (yes/no, pick, rate). Jev's image `box` questions aren't wrapped.
- The TypeSafe SDK is pre-1.0 and has changed its question types between minor versions; it is pinned to `0.7.5`, and the model to `jev-1.14.0`.
- The Jev adapter forces IPv4 by default (`prefer_ipv4`): on some networks the IPv6 address of `api.typesafe.ai` accepts no connection and the first request of every process waited ~21 s before falling back (measured; 0.3 s with IPv4 only). Pass `prefer_ipv4=False` if your network needs IPv6.
- Cost figures are estimates from the list price in `types.py`, not from billing.
- The tests check the mapping against the response shape in TypeSafe's docs; they don't prove the live API still matches.

## Privacy

Everything passed to the judge as `state` is **sent to TypeSafe's servers**. Their documentation (checked 2026-10-30) does not say where that data is processed. TypeSafe states it does not train on user data.

**Jev is used because, as of today, it is the only model of its kind on the market, not because sending data to a US company is the goal. The plan is to replace it with a local model or a European provider** That is why every tool depends on the `Judge` interface in `jev_core`, never on the TypeSafe SDK directly: a replacement is one new adapter module. Until then:

- Don't send secrets, credentials or other people's personal data as `state`.
- The decision log stores a hash and the length of each state, not the text (unless you turn that on for local debugging).
- With the router mod on, each prompt goes to TypeSafe after secret redaction (best effort, not a guarantee).

## Prior art

Ideas this project is related to. No code from them is used.

- [Instructor](https://github.com/567-labs/instructor) and [Outlines](https://github.com/dottxt-ai/outlines): structured, typed output *from generative LLMs*. Here the typed answers come from a separate judgement model, so the referee is not the writer.
- [RouteLLM](https://github.com/lm-sys/RouteLLM): learned routing between a strong and a weak LLM. The router here instead asks a judge typed questions, logs each decision with probabilities, and runs inside Claude Code on a subscription.
- [LiteLLM](https://github.com/BerriAI/litellm): one interface to many LLM providers. `jev_core` is the same idea at a much smaller scale, for judges rather than generators.

## The Jev toolkit family

| Repository | What it is | Depends on |
|---|---|---|
| **Jev-toolkit-usage** (this one) | `jev_core` (judge interface, Jev adapter, cache, decision log, redaction, settings and data location) and the model/effort router | - |
| [Jev-toolkit-Compiler](https://github.com/Wrenik/Jev-toolkit-Compiler) | context log, search and a compact/clear advisor | usage |
| [Jev-toolkit-Scanner](https://github.com/Wrenik/Jev-toolkit-Scanner) | prompt-injection scanner (experimental) | usage |
| [Jev-toolkit-Monitor](https://github.com/Wrenik/Jev-toolkit-Monitor) | agent monitor (experimental) | usage |
| [Jev-toolkit-FactCheck](https://github.com/Wrenik/Jev-toolkit-FactCheck) | fact checker with hover evidence | usage (Scanner optional) |
| [Jev-toolkit-Sources](https://github.com/Wrenik/Jev-toolkit-Sources) | source restriction (allowlist policy) | usage, FactCheck |

All six on one machine: [docs/INSTALL_ALL.md](https://github.com/Wrenik/Jev-toolkit-usage/blob/main/docs/INSTALL_ALL.md) (a script does it). The links work once the repositories are public.

## Contributing, security, license

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Issues and suggestions are welcome, especially where something is wrong or an existing tool already does it better.

Licensed under the [MIT License](LICENSE).
