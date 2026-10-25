"""Small local authentication layer for the Streamlit prototype.

Credentials are intentionally configurable through environment variables so
the demo defaults never need to be used outside local development.
"""
from __future__ import annotations

import hmac
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    username: str
    role: str
    display_name: str
    scope: str = ""


def _credential(role: str, key: str, default: str) -> str:
    return os.getenv(f"AASE_{role.upper()}_{key}", default).strip()


def _users() -> dict[str, tuple[str, str, str, str]]:
    return {
        "admin": (
            _credential("admin", "USERNAME", "admin"),
            _credential("admin", "PASSWORD", "admin123"),
            "Administrator",
            "",
        ),
        "teacher": (
            _credential("teacher", "USERNAME", "teacher"),
            _credential("teacher", "PASSWORD", "teacher123"),
            "Faculty Portal",
            os.getenv("AASE_TEACHER_NAME", "Dr. Anika Rao").strip(),
        ),
        "student": (
            _credential("student", "USERNAME", "student"),
            _credential("student", "PASSWORD", "student123"),
            "Student Portal",
            os.getenv("AASE_STUDENT_GROUP", "BSc-CS-3A").strip(),
        ),
    }


def authenticate(username: str, password: str) -> User | None:
    """Return the matching user, using constant-time credential comparisons."""
    username = username.strip()
    for role, (configured_username, configured_password, display_name, scope) in _users().items():
        if hmac.compare_digest(username, configured_username) and hmac.compare_digest(password, configured_password):
            return User(username=username, role=role, display_name=display_name, scope=scope)
    return None
