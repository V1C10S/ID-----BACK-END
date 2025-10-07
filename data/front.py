from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Any
from datetime import datetime, timezone

# --- PATH DA LISTA.JSON ---

BASE_DIR = Path(__file__).resolve().parents[1]
LISTA_PATH = BASE_DIR / "lista.json"

# --- LENDA A LISTA.JSON ---

def _read_lista() -> List[Dict[str, Any]]:
    if not LISTA_PATH.exists():
        return []
    try:
        return json.loads(LISTA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    
# --- MUDANDO A LISTA.JSON ---

def _write_lista(data: List[Dict[str, Any]]):
    tmp = LISTA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(LISTA_PATH)

def mark_verified(username: str) -> bool:
    """Marca verificacao=true (e adiciona verificado_em) para um username em lista.json."""
    data = _read_lista()
    found = False
    for u in data:
        if u.get("username") == username:
            u["verificacao"] = True
            u["verificado_em"] = datetime.now(timezone.utc).isoformat()
            found = True
            break
    if found:
        _write_lista(data)
    return found

# --- RETORNANDO A VERIFICAÇÃO DO TOKEN ---

def is_verified(username: str) -> bool:
    """Retorna True se o usuário já estiver verificado."""
    data = _read_lista()
    for u in data:
        if u.get("username") == username:
            return bool(u.get("verificacao", False))
    return False

def latest_pending() -> dict | None:
    """Retorna o último registro com verificacao=false (ou None)."""
    data = _read_lista()
    pend = [u for u in data if not u.get("verificacao", False)]
    return pend[-1] if pend else None
