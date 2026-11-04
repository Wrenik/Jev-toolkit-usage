"""JEV_JUDGE=module:factory and the jev_core.judges entry point group."""

import sys
import types
from importlib import metadata

import pytest

from jev_core import config
from jev_core.fake import FakeJudge
from jev_core.judge import JudgeConfigError


@pytest.fixture
def plugin_module(monkeypatch):
    mod = types.ModuleType("my_local_judge")
    mod.make = lambda: FakeJudge(model="local-1")
    mod.bad = lambda: object()
    monkeypatch.setitem(sys.modules, "my_local_judge", mod)
    return mod


def test_module_factory_is_loaded_and_wrapped(plugin_module, monkeypatch, tmp_path):
    monkeypatch.setenv("JEV_JUDGE", "my_local_judge:make")
    judge = config.default_judge(var_dir=tmp_path)
    assert judge.model == "local-1"


def test_factory_returning_a_non_judge_is_a_config_error(plugin_module):
    with pytest.raises(JudgeConfigError, match="protocol"):
        config.load_plugin_judge("my_local_judge:bad")


def test_missing_module_or_attribute_is_a_config_error(plugin_module):
    with pytest.raises(JudgeConfigError, match="could not load"):
        config.load_plugin_judge("no_such_module_xyz:make")
    with pytest.raises(JudgeConfigError, match="could not load"):
        config.load_plugin_judge("my_local_judge:nope")


def test_unknown_plain_name_lists_the_options():
    with pytest.raises(JudgeConfigError, match="entry point"):
        config.load_plugin_judge("definitely-not-registered")


def test_entry_point_name_is_resolved(plugin_module, monkeypatch):
    class EP:
        name = "local"

        @staticmethod
        def load():
            return plugin_module.make

    monkeypatch.setattr(
        metadata, "entry_points", lambda group: [EP()] if group == config.JUDGE_ENTRY_POINT_GROUP else []
    )
    assert config.load_plugin_judge("local").model == "local-1"
