# Jev-toolkit-usage v0.1.0 (draft release notes)

First public release. **Alpha**: a learning project, small and tested offline, not a production router.

## What it is
- `jev_core`: a `Judge` interface for typed answers (yes/no with probability, pick one, rate on a scale), a TypeSafe Jev
  adapter, an offline fake judge, a verdict cache, a decision log, secret redaction and a shared data location (`JEV_HOME`).
- `jev_router` and the `jev-router` Claude Code mod: asks the judge how big each prompt is and picks the Claude model and
  effort, or only suggests (`advise`, the default). Steps down a tier only when that does not throw away a warm prompt cache.

## Try it in two minutes (no key)
```
pip install -e ".[dev]"
python -m jev_router demo
python -m pytest
```

## Status honesty
- Thresholds in the router are first guesses, tuned on a handful of prompts.
- Live calls to Jev work, but no automated test runs against the live API.
- Prompts go to TypeSafe's servers after best-effort secret redaction; where they are processed is not documented by
  TypeSafe. Plan: replace Jev with a local or European judge behind the same interface.
- The mod needs Claude Code with mod support and Python 3.11+ with this package installed.

## Known limits
Text questions only; SDK pinned to `typesafe-sdk==0.7.5` and model to `jev-1.14.0`; cost figures are list-price estimates.

## Suggested GitHub settings (not applied)
- Description: "A judgement model (TypeSafe Jev) next to an LLM: typed yes/no/pick/rate decisions, plus a model/effort router for Claude Code."
- Topics: `llm`, `llm-routing`, `llm-judge`, `claude-code`, `claude-code-plugin`, `typesafe`, `python`, `learning-project`
- Tag `v0.1.0`; mark as pre-release; attach no build artifacts.
