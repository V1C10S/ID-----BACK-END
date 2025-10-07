from flask import Blueprint, request, jsonify
from data.criar_users import carregar_users
import bcrypt
from data.lista import is_verified

# --- BLUEPRINTS ---

login_bp = Blueprint('login', __name__)

# ===== METODOS 'GET' & 'POST' =====

@login_bp.route('/login', methods=['POST'])

def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password').encode('utf-8')

# ===== PUXANDO DOS ARQUIVOS .JSON =====

    usuarios = carregar_users()
    user = next((usuario for usuario in usuarios if usuario['username'] == username), None)

    if not is_verified(username=user["username"], email=user.get("email1")):
        return jsonify({
        "success": False,
        "error": "email_not_verified",
        "message": "Confirme seu e-mail para continuar."
    }), 403

# --- PROTOCOLO 200 ACCEPT / PROTOCOLO 400 FAILED ---

    if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
        return jsonify({"success": True, "message": "Login realizado com sucesso!"}), 200
    else:
        return jsonify({"success": False, "message": "Usuário ou senha incorretos"}), 401