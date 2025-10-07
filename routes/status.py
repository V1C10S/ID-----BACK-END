from flask import Blueprint

# --- BLUEPRINTS ---

status_bp = Blueprint('status', __name__)

# --- STATUS.PY ---

@status_bp.route("/status")
def backend_status():
    return "A TODO VAPOR"
