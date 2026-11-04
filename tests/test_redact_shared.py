"""All tools must redact the same secret formats: one shared implementation (`jev_core.redact`); the sibling tools' own entry points are tested in their repos."""

import pytest

from jev_core.redact import redact as core_redact
from jev_router.redact import redact as router_redact

SECRETS = {
    "stripe": "sk_live_4eC39HqLyjWDarjtT1zdp7dc",
    "google": "AIzaSyA-1234567890abcdefghijklmnopqrstuv",
    "cookie": "Cookie: session=abcdef1234567890abcdef1234567890",
    "github": "ghp_abcdefghijklmnopqrstuvwxyz0123456789AB",
    "aws": "AKIAABCDEFGHIJKLMNOP",
    "pem": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
    "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcdefghijk",
    "url_password": "postgres://admin:Sup3rS3cret@db.internal/app",
}


@pytest.mark.parametrize("name", sorted(SECRETS))
def test_every_entry_point_redacts_every_format(name):
    secret = SECRETS[name]
    assert secret not in core_redact(secret)[0]
    assert secret not in router_redact(secret)[0]
