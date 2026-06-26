"""
Session persistence across F5 / page refresh.
Dùng cookie để lưu token trong browser, server lưu mapping token → user trong file JSON.
Không cần thêm package — chỉ dùng st.context.headers + st.components.v1.html.
"""
import json
import secrets
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_SESSION_FILE = Path(__file__).parent.parent / ".sessions.json"
_COOKIE_NAME  = "mml_session"
_MAX_AGE_SEC  = 30 * 24 * 3600  # 30 ngày

# Server-side store (module-level, shared across tất cả connections trong cùng process)
_SESSIONS: dict[str, dict] = {}


def _load() -> None:
    global _SESSIONS
    try:
        if _SESSION_FILE.exists():
            raw  = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
            now  = time.time()
            _SESSIONS = {k: v for k, v in raw.items() if v.get("_exp", 0) > now}
    except Exception:
        _SESSIONS = {}


def _save() -> None:
    try:
        _SESSION_FILE.write_text(
            json.dumps(_SESSIONS, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


# Nạp khi module được import lần đầu
_load()


# ─── Public API ──────────────────────────────────────────────

def create_session(user: dict) -> str:
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = {**user, "_exp": time.time() + _MAX_AGE_SEC}
    _save()
    return token


def get_session(token: str) -> dict | None:
    if not token:
        return None
    entry = _SESSIONS.get(token)
    if not entry:
        _load()
        entry = _SESSIONS.get(token)
    if not entry:
        return None
    if entry.get("_exp", 0) < time.time():
        delete_session(token)
        return None
    return {k: v for k, v in entry.items() if not k.startswith("_")}


def delete_session(token: str) -> None:
    _SESSIONS.pop(token, None)
    _save()


def write_session_cookie(token: str) -> None:
    """Ghi cookie vào browser qua JavaScript (iframe component)."""
    components.html(
        f'<script>document.cookie="{_COOKIE_NAME}={token};'
        f'max-age={_MAX_AGE_SEC};path=/;SameSite=Strict";</script>',
        height=0,
    )


def clear_session_cookie() -> None:
    """Xóa cookie khỏi browser."""
    components.html(
        f'<script>document.cookie="{_COOKIE_NAME}=;max-age=0;path=/";</script>',
        height=0,
    )


def read_session_cookie() -> str | None:
    """Đọc cookie từ HTTP request headers (st.context.headers — Streamlit >= 1.37)."""
    try:
        cookies_header = st.context.headers.get("cookie", "")
    except AttributeError:
        return None
    for part in cookies_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == _COOKIE_NAME:
            return v.strip() or None
    return None
