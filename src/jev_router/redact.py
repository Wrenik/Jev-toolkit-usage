"""Compatibility shim: the redaction code lives in `jev_core.redact` and is shared by every tool."""

from jev_core.redact import redact, redact_personal

__all__ = ["redact", "redact_personal"]
