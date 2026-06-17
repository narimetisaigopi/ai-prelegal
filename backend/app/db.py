import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .config import DATA_DIR, DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(reset: bool = True) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if reset and Path(DB_PATH).exists():
        Path(DB_PATH).unlink()

    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            );
            """
        )


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def create_user(email: str, password_hash: str) -> dict:
    ts = now_iso()
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, ts),
        )
        user_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row)


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT id, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def list_documents(owner_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, owner_id, title, doc_type, content_json, created_at, updated_at
            FROM documents
            WHERE owner_id = ?
            ORDER BY updated_at DESC
            """,
            (owner_id,),
        ).fetchall()
    return [_row_to_doc(row) for row in rows]


def create_document(owner_id: int, title: str, doc_type: str, content: dict) -> dict:
    ts = now_iso()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO documents (owner_id, title, doc_type, content_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (owner_id, title, doc_type, json.dumps(content), ts, ts),
        )
        doc_id = cursor.lastrowid
        row = conn.execute(
            """
            SELECT id, owner_id, title, doc_type, content_json, created_at, updated_at
            FROM documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()
    return _row_to_doc(row)


def get_document(doc_id: int, owner_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, owner_id, title, doc_type, content_json, created_at, updated_at
            FROM documents
            WHERE id = ? AND owner_id = ?
            """,
            (doc_id, owner_id),
        ).fetchone()
    return _row_to_doc(row) if row else None


def update_document(
    doc_id: int,
    owner_id: int,
    *,
    title: str | None,
    doc_type: str | None,
    content: dict | None,
) -> dict | None:
    existing = get_document(doc_id, owner_id)
    if not existing:
        return None

    new_title = title if title is not None else existing["title"]
    new_doc_type = doc_type if doc_type is not None else existing["doc_type"]
    new_content = content if content is not None else existing["content"]

    with _connect() as conn:
        conn.execute(
            """
            UPDATE documents
            SET title = ?, doc_type = ?, content_json = ?, updated_at = ?
            WHERE id = ? AND owner_id = ?
            """,
            (new_title, new_doc_type, json.dumps(new_content), now_iso(), doc_id, owner_id),
        )

    return get_document(doc_id, owner_id)


def delete_document(doc_id: int, owner_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE id = ? AND owner_id = ?",
            (doc_id, owner_id),
        )
    return cursor.rowcount > 0


def _row_to_doc(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "owner_id": row["owner_id"],
        "title": row["title"],
        "doc_type": row["doc_type"],
        "content": json.loads(row["content_json"]),
        "created_at": datetime.fromisoformat(row["created_at"]),
        "updated_at": datetime.fromisoformat(row["updated_at"]),
    }
