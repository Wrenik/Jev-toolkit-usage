"""The router server (and every sibling tool's server, in its own repo) must use the one guarded handler."""

from pathlib import Path

from jev_core.fake import FakeJudge
from jev_core.localserver import GuardedHandler


def test_router_handler_is_the_guarded_handler():
    from jev_router.server import MAX_BODY_BYTES, make_handler

    handler = make_handler(FakeJudge(), Path("unused.jsonl"))
    assert issubclass(handler, GuardedHandler)
    assert handler.HEADER == "X-Jev-Router" and handler.MAX_BODY_BYTES == MAX_BODY_BYTES
