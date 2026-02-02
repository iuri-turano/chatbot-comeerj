"""
Authentication module - register, login, session management.
"""

import re
import bcrypt
from typing import Optional, Dict, Tuple
from fastapi import Request

import database


def _validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def register_user(email: str, password: str, display_name: str = "Anônimo") -> Tuple[bool, Dict]:
    email = email.strip().lower()

    if not _validate_email(email):
        return False, {"error": "Email inválido."}

    if len(password) < 6:
        return False, {"error": "A senha deve ter pelo menos 6 caracteres."}

    if not display_name.strip():
        display_name = "Anônimo"

    existing = database.get_user_by_email(email)
    if existing:
        return False, {"error": "Este email já está cadastrado."}

    password_hash = _hash_password(password)
    user_id = database.create_user(email, password_hash, display_name.strip())
    token = database.create_session(user_id)

    return True, {
        "token": token,
        "user": {
            "id": user_id,
            "email": email,
            "display_name": display_name.strip()
        }
    }


def login_user(email: str, password: str) -> Tuple[bool, Dict]:
    email = email.strip().lower()

    user = database.get_user_by_email(email)
    if not user:
        return False, {"error": "Email ou senha incorretos."}

    if not _verify_password(password, user["password_hash"]):
        return False, {"error": "Email ou senha incorretos."}

    token = database.create_session(user["id"])

    return True, {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "display_name": user["display_name"]
        }
    }


def get_current_user(token: str) -> Optional[Dict]:
    if not token:
        return None
    return database.validate_session(token)


def logout_user(token: str):
    if token:
        database.delete_session(token)


def get_optional_user(request: Request) -> Optional[Dict]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    return get_current_user(token)
