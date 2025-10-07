from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app, make_response, redirect
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from typing import Dict, Any
from data.front import mark_verified
from pathlib import Path
import json

# --- BLUEPRINTS ---

verif_bp = Blueprint("verif", __name__, url_prefix="/verif")

# --- PATH CRIADOS ---

ROOT = Path(__file__).resolve().parents[1]
USED_TOKENS_PATH = ROOT / "tokens_used.json"

# --- VALIDADE DO TOKEN ---

TOKEN_MAX_AGE = 24 * 3600

def _serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY") or current_app.config.get("MAIL_PASSWORD")
    if not secret:
        raise RuntimeError("SECRET_KEY (ou MAIL_PASSWORD) não configurado")
    return URLSafeTimedSerializer(secret, salt="email-confirm-salt")

def _load_token(token: str, max_age: int = TOKEN_MAX_AGE) -> Dict[str, Any]:
    return _serializer().loads(token, max_age=max_age)

# --- MENSAGEM DE CONFIRMAÇÃO FRONT-END ---

def _html(status: int, html_msg: str):
    html = f"""
    <html>
      <head><meta charset="utf-8"><title>Verificação</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 720px; margin: 40px auto;">
        <div style="padding: 24px; border: 1px solid #e5e7eb; border-radius: 10px;">
          <h2>Status da verificação</h2>
          <p>{html_msg}</p>
          <hr/>
          <small>Você pode fechar esta aba.</small>
        </div>
      </body>
    </html>
    """
    resp = make_response(html, status)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

# --- JTI PARA TER TOKEN UNICO ---

def _read_used() -> set[str]:
    if not USED_TOKENS_PATH.exists():
        return set()
    try:
        data = json.loads(USED_TOKENS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(str(x) for x in data)
        return set()
    except Exception:
        return set()
    
# --- JSON DE CONFIRMAÇÃO ---

def _write_used(jtis: set[str]):
    tmp = USED_TOKENS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(sorted(list(jtis)), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(USED_TOKENS_PATH)

def _is_used(jti: str) -> bool:
    return jti in _read_used()

def _mark_used(jti: str):
    jtis = _read_used()
    jtis.add(jti)
    _write_used(jtis)

# --- VERIF.PY ---

@verif_bp.get("/confirm")
def confirm_by_token():
    token = request.args.get("token")
    if not token:
        
        fail_url = current_app.config.get("VERIF_FAIL_URL")
        if fail_url:
            return redirect(f"{fail_url}?error=TokenAusente")
        return _html(400, "Token ausente.")

    try:
        data = _load_token(token)
    except SignatureExpired:
        fail_url = current_app.config.get("VERIF_FAIL_URL")
        if fail_url:
            return redirect(f"{fail_url}?error=TokenExpirado")
        return _html(400, "Token expirado. Solicite novo e-mail.")
    except BadSignature:
        fail_url = current_app.config.get("VERIF_FAIL_URL")
        if fail_url:
            return redirect(f"{fail_url}?error=TokenInvalido")
        return _html(400, "Token inválido.")

    username = data.get("username")
    jti = data.get("jti")  
    if not username or not jti:
        fail_url = current_app.config.get("VERIF_FAIL_URL")
        if fail_url:
            return redirect(f"{fail_url}?error=TokenMalformado")
        return _html(400, "Token malformado.")

    
# --- NEGANDO GET DE TOKEN ---

    if _is_used(jti):
        fail_url = current_app.config.get("VERIF_FAIL_URL")
        if fail_url:
            return redirect(f"{fail_url}?error=TokenJaUsado")
        return _html(400, "Este link de verificação já foi usado.")

# --- VENDO LISTA.JSON ---

    ok = mark_verified(username)
    if not ok:
        fail_url = current_app.config.get("VERIF_FAIL_URL")
        if fail_url:
            return redirect(f"{fail_url}?error=UsuarioNaoEncontrado")
        return _html(404, f"Usuário '{username}' não encontrado em lista.json.")

    _mark_used(jti)

# --- DIRECIONANDO PARA VERIFICADO/PAGE.TSX ---

    success_url = current_app.config.get("http://localhost:3000/verificado")
    if success_url:
        return redirect(f"{success_url}?ok=1&u={username}")
    return _html(200, f"E-mail verificado para <b>{username}</b>. Obrigado!")

# --- SEM REGISTRO ---

@verif_bp.post("/confirm")
def confirm_by_username():
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    if not username:
        return jsonify({"ok": False, "error": "Informe 'username' no body"}), 400

    if mark_verified(username):
        return jsonify({"ok": True, "username": username, "verified": True}), 200
    return jsonify({"ok": False, "error": "Usuário não encontrado no lista.json"}), 404

# --- DEBUGAS ---

@verif_bp.get("/debug")
def verif_debug():
    return jsonify({
        "has_secret": bool(current_app.config.get("SECRET_KEY") or current_app.config.get("MAIL_PASSWORD")),
        "VERIF_SUCCESS_URL": current_app.config.get("VERIF_SUCCESS_URL"),
        "VERIF_FAIL_URL": current_app.config.get("VERIF_FAIL_URL"),
        "used_count": len(_read_used()),
    })
