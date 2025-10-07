from __future__ import annotations
from flask import Blueprint, jsonify, current_app, request
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from urllib.parse import urljoin
from pathlib import Path
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.utils import formataddr

import os, json
import uuid
import smtplib


# --- BLUEPRINTS ---

bulk_bp = Blueprint("bulk", __name__, url_prefix="/bulk")

# --- PATH CRIADOS ---

ROOT = Path(__file__).resolve().parents[1]
LISTA_PATH = ROOT / "lista.json"

# --- DEF DA KEY ---

def _cfg(key: str, default=None):
    try:
        val = current_app.config.get(key)
        if val is not None:
            return val
    except Exception:
        pass
    env = os.getenv(key)
    return env if env is not None else default

# --- CRIANDO EMAIL AUTOMÁTICO ---

def _mail_sender_tuple():
    sender = _cfg("MAIL_DEFAULT_SENDER")
    if sender:
        return sender

    return (_cfg("MAIL_FROM_NAME", "Aether Digital"),
            _cfg("MAIL_FROM_EMAIL", _cfg("MAIL_USERNAME", "no-reply@example.com")))

# --- VENDO A LISTA.JSON ---

def _read_lista() -> List[Dict[str, Any]]:
    if not LISTA_PATH.exists():
        return []
    try:
        return json.loads(LISTA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

# --- CRIANDO KEY ---

def _serializer() -> URLSafeTimedSerializer:
    secret = _cfg("SECRET_KEY", None)
    if not secret:

        secret = _cfg("MAIL_PASSWORD", None)
    if not secret:
        raise RuntimeError("SECRET_KEY não configurado (defina em app.config ou env).")
    return URLSafeTimedSerializer(secret, salt="email-confirm-salt")

def _make_token(username: str, jti: str) -> str:
    return _serializer().dumps({"username": username, "jti": jti})

# --- PADRONIZANDO EMAIL ---

def _render_email_html(username: str, confirm_url: str) -> str:
    return f"""
      <div style="font-family: Arial, sans-serif; max-width: 520px; margin:auto;">
        <h2>Confirme seu e-mail</h2>
        <p>Olá, <strong>{username}</strong>!</p>
        <p>Clique no botão abaixo para confirmar seu e-mail:</p>
        <p style="text-align:center; margin: 28px 0;">
          <a href="{confirm_url}"
             style="background:#2563eb; color:#fff; text-decoration:none; padding:12px 18px; border-radius:8px; display:inline-block;">
             Confirmar e-mail
          </a>
        </p>
        <p>Se você não solicitou essa verificação, ignore este e-mail.</p>
        <hr/>
        <small>Link: <a href="{confirm_url}">{confirm_url}</a></small>
      </div>
    """

def _base_url() -> str:
    return _cfg("BACKEND_BASE_URL", request.host_url) 

# --- MANDANDO EMAIL ---

def _send_mail(to_email: str, subject: str, html: str):

    mail_ext = current_app.extensions.get("mail")
    if mail_ext is not None:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=html,
            sender=_mail_sender_tuple(),
        )
        mail_ext.send(msg)
        return
    
# --- PEGANDO LOGIN DO APP.PY ---

    MAIL_SERVER = _cfg("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(_cfg("MAIL_PORT", "587"))
    MAIL_USE_TLS = str(_cfg("MAIL_USE_TLS", "true")).lower() == "true"
    MAIL_USERNAME = _cfg("MAIL_USERNAME")
    MAIL_PASSWORD = _cfg("MAIL_PASSWORD")
    FROM_NAME, FROM_EMAIL = _mail_sender_tuple()

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise RuntimeError("Credenciais SMTP ausentes: defina MAIL_USERNAME e MAIL_PASSWORD (App Password).")

# --- FORMATANDO EMAIL ---

    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = to_email

    if MAIL_USE_TLS:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as s:
            s.ehlo()
            s.starttls()
            s.login(MAIL_USERNAME, MAIL_PASSWORD)
            s.send_message(msg)
    else:
        with smtplib.SMTP_SSL(MAIL_SERVER, 465) as s:
            s.login(MAIL_USERNAME, MAIL_PASSWORD)
            s.send_message(msg)

# --- VENDO PARA QUAL EMAIL VAI ---

def _send_to(users: List[Dict[str, Any]]) -> Dict[str, Any]:
    sent, results, errors = 0, [], []
    for u in users:
        username = u.get("username")
        email = u.get("email1")
        if not username or not email:
            errors.append({"user": u, "error": "username/email faltando"})
            continue

# --- FAZENDU TOKEN JTI ---

        try:
            jti = uuid.uuid4().hex
            token = _make_token(username, jti)  
            confirm_url = urljoin(_base_url(), f"/verif/confirm?token={token}")

            html = _render_email_html(username, confirm_url)
            _send_mail(email, "Confirme seu e-mail", html)
            sent += 1

# --- MANDANDO TOKEN JTI ---

            results.append({
                "username": username,
                "email1": email,
                "confirm_url": confirm_url,
                "jti": jti
            })

            current_app.logger.info(f"[bulk] enviado → {username} <{email}> (jti={jti})")

# --- ERROR ---
            
        except Exception as e:
            msg = str(e)
            errors.append({"username": username, "email1": email, "error": msg})
            current_app.logger.exception(f"[bulk] erro {username} <{email}>: {msg}")
    return {"ok": True, "sent": sent, "results": results, "errors": errors}

# --- BULK.PY ---

@bulk_bp.post("/send-all")
def send_all():
    lista = _read_lista()
    pendentes = [u for u in lista if not u.get("verificacao", False)]
    if not pendentes:
        return jsonify({"ok": True, "sent": 0, "message": "Nenhum pendente."}), 200
    return jsonify(_send_to(pendentes)), 200

# --- GET/POST DO EMAIL ---

@bulk_bp.post("/send-one")
def send_one():
    body = request.get_json(silent=True) or {}
    username_req: Optional[str] = body.get("username")
    email_req: Optional[str] = body.get("email1")

# --- VERIFICAÇÃO TOKEN ---

    lista = _read_lista()
    cand = None
    if username_req:
        cand = next((u for u in lista if u.get("username") == username_req and not u.get("verificacao", False)), None)
    elif email_req:
        cand = next((u for u in lista if u.get("email1") == email_req and not u.get("verificacao", False)), None)
    else:
        return jsonify({"ok": False, "error": "Envie 'username' ou 'email1' no body"}), 400

    if not cand:
        return jsonify({"ok": True, "sent": 0, "message": "Não encontrado ou já verificado."}), 200
    return jsonify(_send_to([cand])), 200

# --- MANDANDO PARA AS CONTAS NOVAS ---

@bulk_bp.post("/send-newest")
def send_newest():
    current_app.logger.info("[bulk/send-newest] chamado")
    lista = _read_lista()
    pendentes = [u for u in lista if not u.get("verificacao", False)]
    if not pendentes:
        return jsonify({"ok": True, "sent": 0, "message": "Nenhum pendente."}), 200
    return jsonify(_send_to([pendentes[-1]])), 200

