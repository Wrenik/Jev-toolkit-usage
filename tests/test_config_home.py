"""JEV_HOME data location, development compatibility and the shared .env fallback."""

from pathlib import Path

from jev_core import config


def test_home_defaults_to_dot_jev_toolkit(monkeypatch):
    monkeypatch.delenv("JEV_HOME")
    assert config.home() == Path.home() / ".jev-toolkit"


def test_explicit_jev_home_wins_for_var_even_in_a_dev_checkout(tmp_path, monkeypatch):
    checkout = tmp_path / "repo"
    (checkout / "src" / "jev_core").mkdir(parents=True)
    monkeypatch.chdir(checkout)
    assert config.var_path() == Path(config.home()) / "var"


def test_dev_checkout_uses_its_own_var_when_jev_home_is_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("JEV_HOME")
    checkout = tmp_path / "repo"
    (checkout / "src" / "jev_core").mkdir(parents=True)
    monkeypatch.chdir(checkout)
    assert config.var_path() == checkout.resolve() / "var"


def test_var_folder_with_toolkit_files_counts_but_a_foreign_var_folder_does_not(tmp_path, monkeypatch):
    monkeypatch.delenv("JEV_HOME")
    monkeypatch.setenv("HOME", str(tmp_path / "h"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "h"))
    ours, foreign = tmp_path / "ours", tmp_path / "foreign"
    (ours / "var").mkdir(parents=True)
    (ours / "var" / "judge-log.jsonl").write_text("", encoding="utf-8")
    (foreign / "var").mkdir(parents=True)  # someone else's project that happens to have a var/ folder
    monkeypatch.chdir(ours)
    assert config.var_path() == ours.resolve() / "var"
    monkeypatch.chdir(foreign)
    assert config.var_path() == Path.home() / ".jev-toolkit" / "var"


def test_env_in_jev_home_is_the_shared_fallback_and_a_nearer_env_wins(tmp_path, monkeypatch):
    shared = config.home()
    shared.mkdir(parents=True, exist_ok=True)
    (shared / ".env").write_text("TYPESAFE_API_KEY=from-home\nJEV_MODEL=m-home\n", encoding="utf-8")
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    assert config.load_env()["TYPESAFE_API_KEY"] == "from-home"
    (work / ".env").write_text("JEV_MODEL=m-near\n", encoding="utf-8")
    env = config.load_env()
    assert env["JEV_MODEL"] == "m-near" and env["TYPESAFE_API_KEY"] == "from-home"  # merged, nearer wins
    monkeypatch.setenv("JEV_MODEL", "m-env")
    assert config.load_env()["JEV_MODEL"] == "m-env"  # real environment beats files


def test_default_judge_writes_under_the_home_var(monkeypatch):
    monkeypatch.setenv("JEV_JUDGE", "fake")
    config.default_judge(tag="t").ask("s", {})
    assert (config.home() / "var" / "judge-log.jsonl").exists()


def test_check_command_names_the_data_location(capsys):
    from jev_core.__main__ import main

    main(["check"])
    assert "data home (JEV_HOME)" in capsys.readouterr().out
