from flask import Blueprint, request, jsonify, current_app
from data.criar_users import salvar_user, carregar_users
from data.criar_simple import salvar_simple
from data.lista import sync_lista
import bcrypt
import requests 

# --- BLUEPRINTS ---

sign_bp = Blueprint('sign', __name__)

# --- SIGN.PY ---

@sign_bp.route('/sign', methods=['POST'])
def signup():
    if not request.is_json:
        return jsonify({"success": False, "field": "content-type", "message": "Use Content-Type: application/json"}), 415

    data = request.get_json(silent=True) or {}
    print("[/sign] payload:", data)

# --- PEDINDO AS INFORMAÇÕES ---

    required = ["username", "password", "email1", "email2", "nascimento", "cpf"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"success": False, "field": ",".join(missing), "message": "Campos obrigatórios ausentes."}), 400

    username   = str(data["username"]).strip()
    password   = str(data["password"])
    email1     = str(data["email1"]).strip().lower()
    email2     = str(data["email2"]).strip().lower()
    nascimento = str(data["nascimento"]).strip()
    cpf_raw    = "".join(ch for ch in str(data["cpf"]) if ch.isdigit())
    cpf        = data["cpf"]

# --- CONFIRMANDO OS EMAILS ---

    if email1 != email2:
        return jsonify({"success": False, "field": "email2", "message": "Emails não coincidem."}), 400

    usuarios = carregar_users() or []
    for usuario in usuarios:
        u_email1 = str(usuario.get("email1","")).lower()
        u_email2 = str(usuario.get("email2","")).lower()
        u_cpfraw = "".join(ch for ch in str(usuario.get("cpf","")) if ch.isdigit())

        if usuario.get('username') == username:
            return jsonify({"success": False, "field": "username", "message": "Usuário já existe."}), 400
        if u_email1 in (email1, email2) or u_email2 in (email1, email2):
            return jsonify({"success": False, "field": "email", "message": "Email já cadastrado."}), 400
        if u_cpfraw == cpf_raw:
            return jsonify({"success": False, "field": "cpf", "message": "CPF já cadastrado."}), 400

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# --- PEDINDO AS INFORMAÇÕES ---

    user_completo = {
        "username": username,
        "email1": email1,
        "email2": email2,
        "password": password_hash,
        "nascimento": nascimento,
        "cpf": cpf
    }

    salvar_user(user_completo)

    try:
        gerado = sync_lista()
        print(f"[/sign] sync_lista OK. total={len(gerado)}")
    except Exception as e:
        print(f"[/sign] ERRO sync_lista: {e}")

# --- CRIANDO LOGIN_SIMPLES.JSON ---

    salvar_simple({"username": username, "password": password_hash})

# --- DANDO EMAIL PARA O BULK.PY ---

    bulk_url = current_app.config.get("BULK_SEND_URL") or f"{request.host_url.rstrip('/')}/bulk/send-newest"
    bulk_resp = None
    try:
        r = requests.post(bulk_url, json={}, timeout=8)
        current_app.logger.info(f"[/sign] bulk resp {r.status_code}: {r.text[:300]}")
        try:
            bulk_resp = r.json()
        except Exception:
            bulk_resp = {"status": r.status_code, "text": r.text}
    except Exception as e:
        current_app.logger.exception(f"[/sign] erro ao chamar bulk: {e}")
        bulk_resp = {"error": str(e)}

# --- RETORNANDO CADASTRO FEITO ---

    return jsonify({
        "success": True,
        "message": "Cadastro realizado!",
        "email": {
            "disparo": "bulk/send-newest",
            "resultado": bulk_resp
        }
    }), 201
