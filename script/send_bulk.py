
# ===================================================================== #
# SCRIPT :: send_bulk.py                                                #
# PROPÓSITO: validar fluxo de envio (ambiente de testes)                #
# POR QUE EXISTE AQUI:                                                  #
# - Repetir cenários de teste sem mexer nos scripts de produção         #
# - Documentar parâmetros e comportamento do envio                      #
# COMO USA:                                                             #
#   python send_bulk.py [--username NOME] [--dry-run]                   #
# NOTAS:                                                                #
# - Compartilha lógica com routes/bulk.py por design                    #
# - Serve como referência rápida do payload                             #   
# STATUS: teste/manual (não é parte da API)                             #
# ===================================================================== #

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from flask import Flask
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer


MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "aetherdigital.sev@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "wegpfourblzpfmug") 
MAIL_DEFAULT_SENDER = (
    os.getenv("MAIL_FROM_NAME", "Aether Digital"),
    os.getenv("MAIL_FROM_EMAIL", MAIL_USERNAME),
)

SECRET_KEY = os.getenv("SECRET_KEY", "troque-por-um-segredo-forte")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5500/")


DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


BASE_DIR = Path(__file__).resolve().parents[1]
LISTA_PATH = BASE_DIR / "lista.json"

TOKEN_MAX_AGE = 24 * 3600  # 24h


def read_lista() -> List[Dict[str, Any]]:
    if not LISTA_PATH.exists():
        print(f"[!] Não achei {LISTA_PATH}")
        return []
    try:
        return json.loads(LISTA_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[!] Erro lendo lista.json: {e}")
        return []


def make_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(SECRET_KEY, salt="email-confirm-salt")


def make_token(username: str) -> str:
    return make_serializer().dumps({"username": username})


def render_email_html(username: str, confirm_url: str) -> str:
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


def send_email(mail: Mail, to: str, subject: str, html: str) -> None:
    if DRY_RUN:
        print(f"[DRY-RUN] Enviaria para {to}: {subject}")
        return
    msg = Message(subject=subject, recipients=[to], html=html, sender=MAIL_DEFAULT_SENDER)
    mail.send(msg)


def main(target_username: Optional[str] = None) -> None:
    
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=SECRET_KEY,
        MAIL_SERVER=MAIL_SERVER,
        MAIL_PORT=MAIL_PORT,
        MAIL_USE_TLS=MAIL_USE_TLS,
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER,
    )
    mail = Mail(app)

    lista = read_lista()
    if not lista:
        print("[i] lista.json vazio/ausente — nada a fazer.")
        return

    if target_username:
        pendentes = [u for u in lista if u.get("username") == target_username and not u.get("verificacao", False)]
    else:
        pendentes = [u for u in lista if not u.get("verificacao", False)]

    print(f"[i] Pendentes: {len(pendentes)}")
    if not pendentes:
        return

    sent = 0
    errors: List[Dict[str, Any]] = []

    with app.app_context():
        for u in pendentes:
            username = u.get("username")
            email = u.get("email1")
            if not username or not email:
                errors.append({"user": u, "error": "username/email faltando"})
                continue

            try:
                token = make_token(username)
                confirm_url = urljoin(BACKEND_BASE_URL, f"/verif/confirm?token={token}")
                html = render_email_html(username, confirm_url)
                send_email(mail, to=email, subject="Confirme seu e-mail", html=html)
                sent += 1
                print(f"✅ Enviado para {username} <{email}>  link={confirm_url}")
            except Exception as e:
                errors.append({"username": username, "email": email, "error": str(e)})
                print(f"❌ Erro ao enviar p/ {username} <{email}>: {e}")

    print(f"\n=== Resultado ===")
    print(f"Enviados: {sent}")
    if errors:
        print("Erros:")
        for e in errors:
            print("  -", e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Envio em massa de confirmação para lista.json")
    parser.add_argument("--username", help="Enviar apenas para este username (opcional)")
    parser.add_argument("--dry-run", action="store_true", help="Não envia; só simula")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["DRY_RUN"] = "true"
    main(target_username=args.username)
