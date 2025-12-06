from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail

# --- REGISTRO ROUTES ---

from routes.login import login_bp
from routes.sign import sign_bp
from routes.verif import verif_bp
from routes.status import status_bp
from routes.listagem import listagem_bp
from routes.bulk import bulk_bp

app = Flask(__name__)

# --- CONFIG ---

app.config.update(

# --- SMTP ---

    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="aetherdigital.sev@gmail.com",
    MAIL_PASSWORD="wegpfourblzpfmug",   
    MAIL_DEFAULT_SENDER=("Aether Digital", "aetherdigital.sev@gmail.com"),

# --- URL'S ---
    BACKEND_BASE_URL="http://localhost:5500/",
    VERIF_SUCCESS_URL="http://localhost:3000/sign?ok=1",  

# --- TOKEN UNICO ---
    SECRET_KEY="um-segredo-forte",


    BULK_SEND_URL="http://localhost:5500/bulk/send-newest",
)

# --- CORS AUTO ---

CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
    expose_headers=["Content-Type"],
)

Mail(app)

# --- BLUEPRINTS ---

app.register_blueprint(login_bp)
app.register_blueprint(sign_bp)
app.register_blueprint(verif_bp)
app.register_blueprint(status_bp)
app.register_blueprint(listagem_bp)
app.register_blueprint(bulk_bp)

# --- CHECKING ---

@app.route("/")
def backend_status():
    return "A TODO VAPOR"

# --- DEBUGAS ---

@app.get("/mail-debug")
def mail_debug():
    has_mail = "mail" in app.extensions
    return jsonify({
        "has_mail_extension": has_mail,
        "MAIL_USERNAME": app.config.get("MAIL_USERNAME"),
        "MAIL_DEFAULT_SENDER": app.config.get("MAIL_DEFAULT_SENDER"),
        "BACKEND_BASE_URL": app.config.get("BACKEND_BASE_URL"),
        "VERIF_SUCCESS_URL": app.config.get("VERIF_SUCCESS_URL"),
    })

if __name__ == "__main__":

# --- PORTA BACK ---
    
    app.run(debug=True, host="0.0.0.0")
