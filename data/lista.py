from pathlib import Path
import json
from typing import List, Dict, Any
from typing import Optional

# --- CRIANDO A LISTA.JSON ---

BASE_DIR = Path(__file__).resolve().parents[1]
USUARIOS_PATH = BASE_DIR / "usuarios.json"
LISTA_PATH = BASE_DIR / "lista.json"

# --- VENDO A LISTA.JSON ---

def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []

def _atomic_write_json(path: Path, data: Any):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

# --- FUNÇÕES PRINCIPAIS ---

def sync_lista() -> List[Dict[str, Any]]:
    """
    Lê usuarios.json e cria lista.json com username, email1 e verificacao=False.
    (O verif.py poderá alterar depois para True)
    """
    usuarios = _load_json_list(USUARIOS_PATH)

    lista = []
    for u in usuarios:
        username = u.get("username")
        email1 = u.get("email1")
        if username and email1:
            lista.append({
                "username": username,
                "email1": email1,
                "verificacao": False
            })

# --- MARCANDO A LISTA.JSON ---

    _atomic_write_json(LISTA_PATH, lista)
    return lista

def read_lista() -> List[Dict[str, Any]]:
    """Lê o conteúdo atual de lista.json"""
    return _load_json_list(LISTA_PATH)

def set_verificacao(username: str, value: bool) -> bool:
    """
    Marca verificacao=True/False para um username em lista.json.
    Retorna True se alterou, False se não encontrou.
    """
    lista = read_lista()
    changed = False
    for item in lista:
        if item.get("username") == username:
            item["verificacao"] = bool(value)
            changed = True
            break
    if changed:
        _atomic_write_json(LISTA_PATH, lista)
    return changed

# --- MUDANDO A VERIFICAÇÃO DE FALSE PARA TRUE ---

def is_verified(username: Optional[str]=None, email: Optional[str]=None) -> bool:
    """
    Retorna True se encontrar em lista.json com verificacao=True
    para o username OU email informado (case-insensitive para email).
    """
    lista = read_lista()
    email_norm = (email or "").strip().lower()
    for u in lista:
        if username and u.get("username") == username and u.get("verificacao", False):
            return True
        if email and str(u.get("email1","")).strip().lower() == email_norm and u.get("verificacao", False):
            return True
    return False