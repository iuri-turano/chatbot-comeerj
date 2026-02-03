"""
SQLite database module for user authentication and chat persistence.
"""

import sqlite3
import uuid
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from config import SQLITE_DB_PATH, SESSION_EXPIRY_HOURS

_write_lock = threading.Lock()


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with _write_lock:
        conn = _get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL DEFAULT 'Anônimo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT DEFAULT 'Conversa sem título',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    sources_json TEXT,
                    full_sources_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
                CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
                CREATE INDEX IF NOT EXISTS idx_conversations_chat_id ON conversations(chat_id);
                CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    anonymous_name TEXT DEFAULT 'Anônimo',
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources_json TEXT,
                    rating TEXT NOT NULL CHECK(rating IN ('good', 'neutral', 'bad')),
                    comment TEXT,
                    conversation_id INTEGER,
                    message_index INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
                CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);
            """)
            conn.commit()
        finally:
            conn.close()


# ============================================================================
# USER OPERATIONS
# ============================================================================

def create_user(email: str, password_hash: str, display_name: str = "Anônimo") -> int:
    with _write_lock:
        conn = _get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
                (email, password_hash, display_name)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()


def get_user_by_email(email: str) -> Optional[Dict]:
    conn = _get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = _get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ============================================================================
# SESSION OPERATIONS
# ============================================================================

def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)
    with _write_lock:
        conn = _get_connection()
        try:
            conn.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires_at.isoformat())
            )
            # Update last_login
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
            return token
        finally:
            conn.close()


def validate_session(token: str) -> Optional[Dict]:
    conn = _get_connection()
    try:
        row = conn.execute(
            """SELECT s.user_id, u.email, u.display_name, s.expires_at
               FROM sessions s JOIN users u ON s.user_id = u.id
               WHERE s.token = ?""",
            (token,)
        ).fetchone()
        if not row:
            return None
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now() > expires_at:
            # Expired - clean up
            delete_session(token)
            return None
        return {
            "id": row["user_id"],
            "email": row["email"],
            "display_name": row["display_name"]
        }
    finally:
        conn.close()


def delete_session(token: str):
    with _write_lock:
        conn = _get_connection()
        try:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()


# ============================================================================
# CONVERSATION OPERATIONS
# ============================================================================

def save_conversation(user_id: int, chat_id: str, title: str, messages_list: List[Dict]) -> int:
    with _write_lock:
        conn = _get_connection()
        try:
            # Upsert conversation
            existing = conn.execute(
                "SELECT id FROM conversations WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id)
            ).fetchone()

            if existing:
                conv_id = existing["id"]
                conn.execute(
                    "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                    (title, datetime.now().isoformat(), conv_id)
                )
                # Clear existing messages and re-insert
                conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            else:
                cursor = conn.execute(
                    "INSERT INTO conversations (chat_id, user_id, title) VALUES (?, ?, ?)",
                    (chat_id, user_id, title)
                )
                conv_id = cursor.lastrowid

            # Insert all messages
            for msg in messages_list:
                sources = msg.get("sources")
                sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
                # full_sources stored separately if present
                full_sources = None
                if sources:
                    full_list = []
                    for s in sources:
                        if "full_content" in s:
                            full_list.append({
                                "full_content": s["full_content"],
                                "source": s.get("source", ""),
                                "page": s.get("page", 0),
                                "display_name": s.get("display_name", ""),
                                "priority_label": s.get("priority_label", "")
                            })
                    if full_list:
                        full_sources = json.dumps(full_list, ensure_ascii=False)

                conn.execute(
                    """INSERT INTO messages (conversation_id, role, content, sources_json, full_sources_json)
                       VALUES (?, ?, ?, ?, ?)""",
                    (conv_id, msg["role"], msg["content"], sources_json, full_sources)
                )

            conn.commit()
            return conv_id
        finally:
            conn.close()


def get_conversations(user_id: int, limit: int = 20) -> List[Dict]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT c.chat_id, c.title, c.created_at, c.updated_at,
                      (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
               FROM conversations c
               WHERE c.user_id = ?
               ORDER BY c.updated_at DESC
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_conversation(user_id: int, chat_id: str) -> Optional[Dict]:
    conn = _get_connection()
    try:
        conv = conn.execute(
            "SELECT * FROM conversations WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        ).fetchone()
        if not conv:
            return None

        messages = conn.execute(
            """SELECT role, content, sources_json, full_sources_json, created_at
               FROM messages WHERE conversation_id = ? ORDER BY id ASC""",
            (conv["id"],)
        ).fetchall()

        msg_list = []
        for m in messages:
            msg = {"role": m["role"], "content": m["content"]}
            if m["sources_json"]:
                sources = json.loads(m["sources_json"])
                # Merge full_sources back if available
                if m["full_sources_json"]:
                    full_sources = json.loads(m["full_sources_json"])
                    full_map = {(fs.get("source", ""), fs.get("page", 0)): fs.get("full_content", "")
                                for fs in full_sources}
                    for s in sources:
                        key = (s.get("source", ""), s.get("page", 0))
                        if key in full_map:
                            s["full_content"] = full_map[key]
                msg["sources"] = sources
            msg_list.append(msg)

        return {
            "chat_id": conv["chat_id"],
            "title": conv["title"],
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"],
            "messages": msg_list
        }
    finally:
        conn.close()


def delete_conversation(user_id: int, chat_id: str) -> bool:
    with _write_lock:
        conn = _get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


# ============================================================================
# FEEDBACK OPERATIONS
# ============================================================================

def save_feedback(user_id: Optional[int], anonymous_name: str, question: str,
                  answer: str, sources_json: Optional[str], rating: str,
                  comment: Optional[str], conversation_id: Optional[int] = None,
                  message_index: Optional[int] = None) -> int:
    with _write_lock:
        conn = _get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO feedback
                   (user_id, anonymous_name, question, answer, sources_json,
                    rating, comment, conversation_id, message_index)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, anonymous_name, question, answer, sources_json,
                 rating, comment, conversation_id, message_index)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()


def get_feedback(limit: int = 50, offset: int = 0,
                 rating_filter: Optional[str] = None) -> List[Dict]:
    conn = _get_connection()
    try:
        query = """SELECT f.*, u.email, u.display_name as user_display_name
                   FROM feedback f
                   LEFT JOIN users u ON f.user_id = u.id"""
        params = []
        if rating_filter:
            query += " WHERE f.rating = ?"
            params.append(rating_filter)
        query += " ORDER BY f.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_feedback_stats() -> Dict:
    conn = _get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM feedback").fetchone()["c"]
        good = conn.execute("SELECT COUNT(*) as c FROM feedback WHERE rating='good'").fetchone()["c"]
        neutral = conn.execute("SELECT COUNT(*) as c FROM feedback WHERE rating='neutral'").fetchone()["c"]
        bad = conn.execute("SELECT COUNT(*) as c FROM feedback WHERE rating='bad'").fetchone()["c"]

        by_month = conn.execute("""
            SELECT strftime('%Y-%m', created_at) as month,
                   COUNT(*) as count,
                   SUM(CASE WHEN rating='good' THEN 1 ELSE 0 END) as good,
                   SUM(CASE WHEN rating='bad' THEN 1 ELSE 0 END) as bad
            FROM feedback
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """).fetchall()

        return {
            "total": total,
            "good": good,
            "neutral": neutral,
            "bad": bad,
            "by_month": [dict(r) for r in by_month]
        }
    finally:
        conn.close()


def get_top_rated_feedback(limit: int = 10) -> List[Dict]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT question, answer, comment, created_at
               FROM feedback
               WHERE rating = 'good'
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
