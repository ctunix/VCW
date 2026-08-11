"""Password-only remote access gate for the VCW Web UI."""

from __future__ import annotations

import hmac
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import gradio as gr


SESSION_COOKIE = "vcw_session"
LOGIN_PATH = "/__vcw_login"
PUBLIC_PATHS = {LOGIN_PATH, "/startup-events"}


def _login_page(error: str = "") -> str:
    error_html = f'<p class="login__error">{error}</p>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>VCW — Login</title><style>
:root{{--bg:#16161e;--surface:#1e1f28;--panel:#2d2e36;--border:#4a5f8f;--focus:#5ccfe6;--primary:#5ccfe6;--accent:#73d0ff;--error:#f07178;--text:#a1a8cf;--bold:#d5d8ec;--muted:#8995bc;}}
*{{box-sizing:border-box}} body{{min-height:100vh;margin:0;padding:16px;display:flex;align-items:center;justify-content:center;background:var(--bg);color:var(--text);font:14px/1.6 "JetBrains Mono","Fira Code",Consolas,monospace}}
.login{{width:min(360px,100%);padding:32px;background:var(--surface);border:1px solid var(--border);border-top:2px solid var(--primary);box-shadow:0 8px 32px #0008}}
.login__logo{{margin:0 0 4px;color:var(--primary);font-size:22px;font-weight:700;letter-spacing:2px}} .login__sub{{margin:0 0 24px;color:var(--muted);font-size:11px}} .login__error{{color:var(--error);font-size:12px}}
.login__input{{width:100%;margin:0 0 16px;padding:10px 12px;background:var(--bg);border:1px solid var(--border);border-radius:2px;color:var(--bold);font:inherit;outline:0}} .login__input:focus{{border-color:var(--focus);box-shadow:0 0 0 2px #5ccfe633}} .login__input::placeholder{{color:var(--muted)}}
.login__button{{width:100%;padding:10px 12px;border:0;border-radius:2px;background:var(--primary);color:var(--bg);cursor:pointer;font:700 14px "JetBrains Mono","Fira Code",Consolas,monospace;letter-spacing:1px}} .login__button:hover{{background:var(--accent)}}
</style></head><body><form class="login" method="post" action="{LOGIN_PATH}"><p class="login__logo">VCW</p><p class="login__sub">voice cloning workflow — access password required</p>{error_html}<input class="login__input" type="password" name="password" placeholder="access password" autofocus autocomplete="current-password"><button class="login__button" type="submit">ENTER</button></form></body></html>"""


def _cookies(scope: dict) -> dict[str, str]:
    raw = dict(scope.get("headers", [])).get(b"cookie", b"").decode("latin-1")
    return {
        key.strip(): value.strip()
        for item in raw.split(";")
        if "=" in item
        for key, value in [item.split("=", 1)]
    }


class PasswordGate:
    """Pure ASGI session gate covering HTTP and WebSocket routes."""

    def __init__(self, app, session_token: str) -> None:
        self.app = app
        self.session_token = session_token

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        if scope.get("path", "") in PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return
        if _cookies(scope).get(SESSION_COOKIE) == self.session_token:
            await self.app(scope, receive, send)
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 4401})
            return
        await HTMLResponse(_login_page(), status_code=401)(scope, receive, send)


def add_password_login(fastapi_app, password: str, secure_cookie: bool) -> None:
    """Install VCW's password-only login on a FastAPI app."""
    session_token = secrets.token_urlsafe(32)

    @fastapi_app.post(LOGIN_PATH)
    async def login(request: Request):
        form = await request.form()
        supplied = str(form.get("password", ""))
        if not hmac.compare_digest(supplied, password):
            return HTMLResponse(_login_page("Wrong password."), status_code=401)
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            SESSION_COOKIE,
            session_token,
            httponly=True,
            samesite="lax",
            secure=secure_cookie,
            path="/",
        )
        return response

    fastapi_app.add_middleware(PasswordGate, session_token=session_token)

def create_protected_app(gradio_blocks, password: str, secure_cookie: bool):
    """Mount Gradio behind one protected parent app.

    Gradio 3.14 creates a fresh FastAPI app inside ``Blocks.launch()``. Mounting
    it explicitly ensures the login gate protects the app that is actually
    served, including queue and upload routes.
    """
    fastapi_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    add_password_login(fastapi_app, password, secure_cookie)
    return gr.mount_gradio_app(fastapi_app, gradio_blocks, path="/")
