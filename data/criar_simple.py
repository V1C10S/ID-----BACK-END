import json

# --- CRIANDO USUARIOS.JSON ---

def salvar_simple(login_data, caminho='logins_simples.json'):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            logins = json.load(f)
    except FileNotFoundError:
        logins = []
    logins.append(login_data)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(logins, f, ensure_ascii=False, indent=2)