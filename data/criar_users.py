import json

# --- CRIANDO USUARIOS.JSON ---

def carregar_users(caminho='usuarios.json'):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
            return usuarios
    except FileNotFoundError:
        return []
    
# --- ALTERANDO USUARIOS.JSON ---

def salvar_user(user_data, caminho='usuarios.json'):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
    except FileNotFoundError:
        usuarios = []
    usuarios.append(user_data)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
