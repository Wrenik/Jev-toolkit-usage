"""jev_core: a small, model-independent judgement layer. See docs/DESIGN.md."""

from importlib import metadata as _metadata

from .cache import CachingJudge
from .config import default_judge, load_env
from .fake import FakeJudge
from .judge import Judge, JudgeConfigError, JudgeError, JudgeUnavailable, pick, rate, yes_no
from .log import LoggingJudge
from .types import Pick, PickAnswer, Question, Rate, RateAnswer, Verdict, YesNo, YesNoAnswer

try:
    __version__ = _metadata.version("jev-toolkit-usage")
except _metadata.PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0+unknown"

__all__ = [
    "__version__",
    "CachingJudge",
    "FakeJudge",
    "Judge",
    "JudgeConfigError",
    "JudgeError",
    "JudgeUnavailable",
    "LoggingJudge",
    "Pick",
    "PickAnswer",
    "Question",
    "Rate",
    "RateAnswer",
    "Verdict",
    "YesNo",
    "YesNoAnswer",
    "default_judge",
    "load_env",
    "pick",
    "rate",
    "yes_no",
]
