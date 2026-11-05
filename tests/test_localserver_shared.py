"""The router server (and every sibling tool's server, in its own repo) must use the one guarded handler."""

from pathlib import Path

from jev_core.fake import FakeJudge
from jev_core.localserver import GuardedHandler


def test_router_handler_is_the_guarded_handler():
    from jev_router.server import MAX_BODY_BYTES, make_handler

    handler = make_handler(FakeJudge(), Path("unused.jsonl"))
    assert issubclass(handler, GuardedHandler)
    assert handler.HEADER == "X-Jev-Router" and handler.MAX_BODY_BYTES == MAX_BODY_BYTES


def test_second_server_cannot_share_a_port_on_windows():
    import os
    import socket

    import pytest

    from jev_core.localserver import GuardedHandler, GuardedServer

    first = GuardedServer(("127.0.0.1", 0), GuardedHandler)
    try:
        port = first.server_address[1]
        if os.name == "nt":
            with pytest.raises(OSError):
                GuardedServer(("127.0.0.1", port), GuardedHandler).server_close()
        else:
            assert GuardedServer.allow_reuse_address is True
        s = socket.socket()
        s.close()
    finally:
        first.server_close()
