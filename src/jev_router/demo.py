"""Offline demo of the router policy: a keyword-driven stand-in for the judge, so no key is needed.

The stand-in only imitates the *shape* of Jev's answers for a few canned prompts; it says nothing
about how well the real judge routes. Run it with `python -m jev_router demo`.
"""

from __future__ import annotations

from jev_core import FakeJudge, Pick, PickAnswer, Rate, RateAnswer, YesNo, YesNoAnswer

from .policy import COMPLEXITY_LEVELS, route

SAMPLES = [
    ("Rename the variable cnt to count in utils.py.", 0.3, "light"),
    ("yes, go ahead", 0.1, "follow"),
    ("Add a --verbose flag to the CLI and document it.", 1.4, "plain"),
    ("Find why the nightly sync loses rows only on Mondays; the cause is unknown.", 3.2, "deep"),
    ("Delete all rows older than a year from the production database.", 2.0, "risky"),
]


def _responder(complexity: float, kind: str):
    def respond(_state, questions):
        yn = {
            "deep": 0.9 if kind == "deep" else 0.2,
            "mechanical": 0.9 if kind == "light" else 0.2,
            "followup": 0.9 if kind == "follow" else 0.1,
            "coding": 0.1 if kind in ("follow", "risky") else 0.8,
            "multi_file": 0.8 if kind == "deep" else 0.2,
        }
        out = {name: YesNoAnswer(p) for name, p in yn.items() if isinstance(questions.get(name), YesNo)}
        risk = {"none": 0.05, "low": 0.15, "high": 0.8} if kind == "risky" else {"none": 0.6, "low": 0.35, "high": 0.05}
        out["risk"] = PickAnswer(max(risk, key=risk.__getitem__), max(risk.values()), risk)
        idx = min(len(COMPLEXITY_LEVELS) - 1, round(complexity))
        probs = {lv: (0.7 if i == idx else 0.075) for i, lv in enumerate(COMPLEXITY_LEVELS)}
        out["complexity"] = RateAnswer(complexity, COMPLEXITY_LEVELS[idx], 0.7, probs)
        assert isinstance(questions["complexity"], Rate) and isinstance(questions["risk"], Pick)
        return out

    return respond


def run_demo() -> int:
    print("Offline demo: canned judge answers, no network. 'previous' is the tier before the prompt.\n")
    previous = None
    for prompt, complexity, kind in SAMPLES:
        decision, _ = route(FakeJudge(_responder(complexity, kind)), prompt, previous)
        print(f"> {prompt}")
        print(f"  -> {decision.tier:<8} {decision.model} / effort {decision.effort}   ({decision.reason})")
        previous = decision.tier
    return 0
