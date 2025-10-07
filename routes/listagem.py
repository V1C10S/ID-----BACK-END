from flask import Blueprint, jsonify
from data.lista import sync_lista, read_lista

# --- BLUEPRINTS ---

listagem_bp = Blueprint("listagem", __name__, url_prefix="/listagem")

# --- LISTAGEM.PY ---

@listagem_bp.get("/")
def get_lista():
    """
    Retorna o conteúdo atual de lista.json.
    Se ainda não existir, retorna [].
    """
    return jsonify(read_lista())

# --- ATUALIZAÇÃO DA LISTA.JSON ---

@listagem_bp.post("/sync")
def post_sync_lista():
    """
    Regera lista.json a partir de usuarios.json e retorna a lista resultante.
    Use isso quando quiser forçar a atualização.
    """

# --- FAZENDO RETORNO DA LISTA ---

    lista = sync_lista()
    return jsonify({"ok": True, "count": len(lista), "lista": lista}), 200
