"""Remove likely secrets from a prompt before it leaves the machine.

Pattern-based, so it is a seatbelt, not a guarantee: it catches the common
key formats and `name = value` assignments of obvious secret names. Anything it
misses is still sent to the judge. The kinds found are logged, never the values.
"""

from __future__ import annotations

import re
import unicodedata

# (kind, pattern). Order matters: specific formats before the generic ones.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)", re.S)),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("npm_token", re.compile(r"\bnpm_[A-Za-z0-9]{30,}")),
    ("aws_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("google_key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("stripe_key", re.compile(r"\b(?:[sr]k|whsec)_(?:live_|test_)?[A-Za-z0-9]{16,}")),
    ("basic_auth_arg", re.compile(r"(?i)(?<=\s)(?:-u|--user)[ =]+['\"]?[^\s:'\"]+:(?!//)[^\s'\"]{3,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("cookie", re.compile(r"(?i)\b((?:set-)?cookie\s*:\s*)[^\r\n]+")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("url_password", re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s@/]+@")),
    # KEY=value / "password": "value" for obvious secret names (env files, JSON, YAML).
    ("assignment", re.compile(
        r"(?i)\b([A-Z0-9_]*(?:api[_-]?key|secret|token|passw(?:or)?d|pwd|private[_-]?key|access[_-]?key)[A-Z0-9_]*)"
        r"([\"']?\s*[:=]\s*[\"']?)(?!\[REDACTED)([^\s\"',;]{6,})"
    )),
]


# Cheap gate: a pattern can only match if one of these lowercase markers occurs in the text, so the
# slow regexes are skipped for the (vast majority of) text that has none. Every marker must be a
# necessary substring of its pattern; tests/test_context_hardening.py checks gated == ungated.
_MARKERS: dict[str, tuple[str, ...]] = {
    "private_key": ("private key",),
    "anthropic_key": ("sk-ant-",),
    "openai_key": ("sk-",),
    "github_token": ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"),
    "npm_token": ("npm_",),
    "basic_auth_arg": ("-u", "--user"),
    "aws_key_id": ("akia", "asia"),
    "slack_token": ("xox",),
    "google_key": ("aiza",),
    "stripe_key": ("sk_", "rk_", "whsec_"),
    "jwt": ("eyj",),
    "cookie": ("cookie",),
    "bearer_token": ("bearer",),
    "url_password": ("://",),
    "assignment": ("api", "secret", "token", "pass", "pwd", "private", "access"),
}


def redact(text: str, gated: bool = True) -> tuple[str, list[str]]:
    """Returns the text with secrets replaced by `[REDACTED:<kind>]`, and the kinds found."""
    found: list[str] = []
    for kind, pattern in _PATTERNS:
        if gated:
            low = text.lower()
            if not any(m in low for m in _MARKERS[kind]):
                continue
        if kind == "cookie":
            def keep_header(m: re.Match[str]) -> str:
                found.append(kind)
                return f"{m.group(1)}[REDACTED:cookie]"

            text = pattern.sub(keep_header, text)
            continue
        if kind == "assignment":
            def keep_name(m: re.Match[str]) -> str:
                found.append(kind)
                return f"{m.group(1)}{m.group(2)}[REDACTED:secret]"

            text = pattern.sub(keep_name, text)
            continue

        def replace(m: re.Match[str], kind: str = kind) -> str:
            found.append(kind)
            return f"[REDACTED:{kind}]"

        text = pattern.sub(replace, text)
    return text, found


# Personal data. Used by the long-term log (which keeps text for years) but NOT by the router: names and
# paths are useful context for the judge, and telephone numbers are too ambiguous to match reliably.
_PERSONAL: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")),
    ("home_path", re.compile(r"""(?i)(?:\b[a-z]:[\\/]+users[\\/]+|/home/|/users/)[^\\/\s"']+""")),
]


def redact_personal(text: str) -> tuple[str, list[str]]:
    """`redact` plus e-mail addresses and home-directory user names. Phone numbers are NOT detected."""
    text, found = redact(text)
    text = unicodedata.normalize("NFKC", text)  # fullwidth look-alikes of "@" and letters
    for kind, pattern in _PERSONAL:
        def replace(m: re.Match[str], kind: str = kind) -> str:
            found.append(kind)
            return f"[REDACTED:{kind}]"

        text = pattern.sub(replace, text)
    return text, found
