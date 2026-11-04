"""Regression tests from the pre-release review (robustness of cache/log/env parsing and the CLIs)."""

import json
import threading

import pytest

from jev_core import CachingJudge, FakeJudge, JudgeUnavailable, LoggingJudge, YesNo, __version__
from jev_core import __main__ as core_main
from jev_core.config import _parse
from jev_router import __main__ as router_main
from jev_router.policy import route, tier_of_model
from jev_router.server import handle_route

Q = {"q": YesNo("Is it?")}


def test_env_parser_accepts_export_comments_and_quotes(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        "﻿# comment\nexport TYPESAFE_API_KEY=abc123 # my key\nJEV_MODEL='jev-1' # pinned\n"
        'A="x # not a comment"\nB=has#hash\n',
        encoding="utf-8",
    )
    v = _parse(f)
    assert v == {"TYPESAFE_API_KEY": "abc123", "JEV_MODEL": "jev-1", "A": "x # not a comment", "B": "has#hash"}


def test_corrupt_cache_file_falls_back_to_memory(tmp_path):
    path = tmp_path / "judge-cache.sqlite"
    path.write_bytes(b"this is not a database" * 50)
    inner = FakeJudge()
    judge = CachingJudge(inner, path)
    judge.ask("s", Q)
    assert judge.ask("s", Q).cached is True and len(inner.calls) == 1


def test_cache_errors_do_not_break_the_call(tmp_path):
    inner = FakeJudge()
    judge = CachingJudge(inner, tmp_path / "c.sqlite")
    judge._db.close()  # every later cache operation now raises sqlite3.ProgrammingError
    assert judge.ask("s", Q)["q"].p_yes == 0.5
    assert len(inner.calls) == 1


def test_log_write_failure_does_not_lose_the_verdict(tmp_path):
    blocker = tmp_path / "log.jsonl"
    judge = LoggingJudge(FakeJudge(), blocker)
    blocker.mkdir()  # the log path is now a directory: open() fails
    assert judge.ask("s", Q)["q"].p_yes == 0.5


def test_cache_is_safe_across_threads(tmp_path):
    inner = FakeJudge()
    judge = CachingJudge(inner, tmp_path / "c.sqlite")
    errors = []

    def work(i):
        try:
            for j in range(20):
                judge.ask(f"state {j % 5}", Q)
        except Exception as err:  # noqa: BLE001
            errors.append(err)

    threads = [threading.Thread(target=work, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors


@pytest.mark.parametrize("bad", [None, 5, ["opus"], {"a": 1}, ""])
def test_malformed_current_model_is_treated_as_unknown(bad):
    assert tier_of_model(bad) is None
    decision, _ = route(FakeJudge(), "hi", current_model=bad)
    assert decision.manages_current is True


def test_handle_route_survives_garbage_fields(tmp_path):
    log = tmp_path / "r.jsonl"
    body = {"prompt": None, "previous_tier": ["x"], "current_model": 7, "context_tokens": "many", "idle_ms": True}
    result = handle_route(FakeJudge(), body, log)
    assert result["ok"] is True
    assert json.loads(log.read_text(encoding="utf-8").splitlines()[0])["ok"] is True


def test_handle_route_fails_open_when_judge_is_down(tmp_path):
    result = handle_route(FakeJudge(fail_with=JudgeUnavailable("down")), {"prompt": "x"}, tmp_path / "r.jsonl")
    assert result["ok"] is False and "JudgeUnavailable" in result["error"]


def test_core_cli_check_reports_missing_key_with_exit_1(capsys):
    assert core_main.main(["check"]) == 1
    out = capsys.readouterr().out
    assert "MISSING" in out and "JEV_JUDGE=fake" in out


def test_core_cli_check_ok_with_fake_judge(monkeypatch, capsys):
    monkeypatch.setenv("JEV_JUDGE", "fake")
    assert core_main.main(["check"]) == 0
    assert "OK" in capsys.readouterr().out


def test_cli_version_and_help_and_unknown(capsys):
    assert core_main.main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out
    assert router_main.main(["--version"]) == 0
    assert router_main.main(["--help"]) == 0
    assert router_main.main(["nonsense"]) == 2
    assert core_main.main(["nonsense"]) == 2


def test_router_serve_bad_port_and_missing_key(capsys):
    assert router_main.main(["serve", "abc"]) == 2
    assert router_main.main(["serve", "8799"]) == 1  # no key configured: friendly message, not a traceback
    assert "cannot start" in capsys.readouterr().out


def test_router_demo_runs_offline(capsys):
    assert router_main.main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "light" in out and "heavy" in out
