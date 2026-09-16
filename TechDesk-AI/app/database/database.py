import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime
import uuid


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "techdesk.db"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USING_POSTGRES = DATABASE_URL.startswith(("postgresql://", "postgres://"))


def get_connection():
    if USING_POSTGRES:
        try:
            import psycopg
            from psycopg.rows import dict_row
            return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=15)
        except ImportError:
            pass

    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return dict(row) if row is not None else None


def rows_to_dict(rows):
    return [dict(r) for r in rows] if rows else []


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'employee',
                department TEXT DEFAULT 'General',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Tickets Table (with priority and SLA support)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                question TEXT NOT NULL,
                intent TEXT DEFAULT 'general',
                department TEXT DEFAULT 'General IT Helpdesk',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'open',
                rating INTEGER DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        # Chat History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                intent TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'Medium',
                agent_type TEXT DEFAULT 'general',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        # Ticket Replies Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                specialist_user_id INTEGER,
                reply TEXT NOT NULL,
                approval_status TEXT DEFAULT 'pending',
                approved_by INTEGER,
                approved_at TEXT,
                knowledge_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
                FOREIGN KEY (specialist_user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        # Notifications Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticket_id TEXT,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
            )
        """)

        # Specialist & IT Knowledge Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                approved_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
    finally:
        conn.close()


# =========================================================
# USERS CRUD
# =========================================================

def save_user(name, email, password_hash, role="employee", department="General"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        email = email.strip().lower()
        cursor.execute("SELECT id FROM users WHERE lower(email) = lower(?)", (email,))
        if cursor.fetchone():
            return None

        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, department)
            VALUES (?, ?, ?, ?, ?)
        """, (name.strip(), email, password_hash, role, department))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_users():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, role, department, created_at FROM users ORDER BY id DESC")
        return rows_to_dict(cursor.fetchall())
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, role, department, created_at FROM users WHERE lower(email) = lower(?)", (email.strip(),))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_login_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, password_hash, role, department, created_at FROM users WHERE lower(email) = lower(?)", (email.strip(),))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, role, department, created_at FROM users WHERE id = ?", (user_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_user_password(user_id, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# SESSIONS
# =========================================================

def save_session(token_hash, user_id, expires_at):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sessions (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
        """, (token_hash, user_id, expires_at))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_session(token_hash, current_time):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.role, u.department, u.created_at
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
        """, (token_hash, current_time))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def delete_session(token_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# CHAT LOGGING
# =========================================================

def save_chat(question, answer, intent="general", priority="Medium", agent_type="general", user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO chats (user_id, question, answer, intent, priority, agent_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, question, answer, intent, priority, agent_type))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_chat_history(user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT c.id, c.user_id, c.question, c.answer, c.intent, c.priority, c.agent_type, c.created_at,
                   u.name as employee_name, u.email as employee_email
            FROM chats c
            LEFT JOIN users u ON u.id = c.user_id
        """
        params = ()
        if user_id is not None:
            query += " WHERE c.user_id = ?"
            params = (user_id,)
        query += " ORDER BY c.id DESC LIMIT 100"
        cursor.execute(query, params)
        return rows_to_dict(cursor.fetchall())
    finally:
        conn.close()


# =========================================================
# TICKETS CRUD (WITH PRIORITY & SLA)
# =========================================================

def save_ticket(question, intent="general", department="General IT Helpdesk", priority="Medium", user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        ticket_id = f"TECH-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        cursor.execute("""
            INSERT INTO tickets (ticket_id, user_id, question, intent, department, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, 'open')
        """, (ticket_id, user_id, question, intent, department, priority))
        conn.commit()
        return ticket_id
    finally:
        conn.close()


def get_tickets(user_id=None, department=None, status_filter=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT t.id, t.ticket_id, t.user_id, t.question, t.intent, t.department, t.priority,
                   t.status, t.rating, t.created_at, t.updated_at,
                   u.name as employee_name, u.email as employee_email,
                   (
                       SELECT tr.reply FROM ticket_replies tr
                       WHERE tr.ticket_id = t.ticket_id
                       ORDER BY tr.id DESC LIMIT 1
                   ) as latest_reply,
                   (
                       SELECT u2.name FROM ticket_replies tr2
                       LEFT JOIN users u2 ON u2.id = tr2.specialist_user_id
                       WHERE tr2.ticket_id = t.ticket_id
                       ORDER BY tr2.id DESC LIMIT 1
                   ) as specialist_name
            FROM tickets t
            LEFT JOIN users u ON u.id = t.user_id
            WHERE 1=1
        """
        params = []
        if user_id is not None:
            query += " AND t.user_id = ?"
            params.append(user_id)
        if department is not None and department != "All":
            query += " AND lower(t.department) = lower(?)"
            params.append(department)
        if status_filter is not None and status_filter != "all":
            query += " AND lower(t.status) = lower(?)"
            params.append(status_filter)

        query += " ORDER BY t.id DESC"
        cursor.execute(query, tuple(params))
        return rows_to_dict(cursor.fetchall())
    finally:
        conn.close()


def get_ticket(ticket_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.*, u.name as employee_name, u.email as employee_email
            FROM tickets t
            LEFT JOIN users u ON u.id = t.user_id
            WHERE t.ticket_id = ?
        """, (ticket_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def assign_ticket_to_user(ticket_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tickets SET user_id = ? WHERE ticket_id = ?", (user_id, ticket_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_ticket_status(ticket_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE tickets
            SET status = ?, updated_at = ?
            WHERE ticket_id = ?
        """, (new_status, now, ticket_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def rate_ticket(ticket_id, rating):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tickets SET rating = ? WHERE ticket_id = ?", (rating, ticket_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# TICKET REPLIES
# =========================================================

def save_ticket_reply(ticket_id, reply, specialist_user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ticket_replies (ticket_id, specialist_user_id, reply)
            VALUES (?, ?, ?)
        """, (ticket_id, specialist_user_id, reply))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_ticket_replies(ticket_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT tr.*, u.name as specialist_name, u.role as specialist_role
            FROM ticket_replies tr
            LEFT JOIN users u ON u.id = tr.specialist_user_id
            WHERE tr.ticket_id = ?
            ORDER BY tr.id ASC
        """, (ticket_id,))
        return rows_to_dict(cursor.fetchall())
    finally:
        conn.close()


def approve_latest_ticket_reply(ticket_id, admin_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, reply FROM ticket_replies
            WHERE ticket_id = ?
            ORDER BY id DESC LIMIT 1
        """, (ticket_id,))
        latest = cursor.fetchone()
        if not latest:
            return None

        # Fetch ticket details
        cursor.execute("SELECT question, intent, department FROM tickets WHERE ticket_id = ?", (ticket_id,))
        tkt = cursor.fetchone()
        if not tkt:
            return None

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Save into it_knowledge table as approved article
        cursor.execute("""
            INSERT INTO it_knowledge (category, title, content, approved_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tkt["intent"], tkt["question"], latest["reply"], admin_user_id, now, now))
        knowledge_id = cursor.lastrowid

        # Mark reply as approved
        cursor.execute("""
            UPDATE ticket_replies
            SET approval_status = 'approved', approved_by = ?, approved_at = ?, knowledge_id = ?
            WHERE id = ?
        """, (admin_user_id, now, knowledge_id, latest["id"]))

        conn.commit()
        return knowledge_id
    finally:
        conn.close()


# =========================================================
# NOTIFICATIONS
# =========================================================

def save_notification(user_id, message, ticket_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO notifications (user_id, ticket_id, message)
            VALUES (?, ?, ?)
        """, (user_id, ticket_id, message))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_notifications(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 50
        """, (user_id,))
        return rows_to_dict(cursor.fetchall())
    finally:
        conn.close()


def mark_notifications_read(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


# =========================================================
# IT KNOWLEDGE MANAGEMENT
# =========================================================

def save_it_knowledge(category, title, content, approved_by=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO it_knowledge (category, title, content, approved_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category, title, content, approved_by, now, now))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_it_knowledge():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM it_knowledge ORDER BY id DESC")
        return rows_to_dict(cursor.fetchall())
    finally:
        conn.close()


def update_it_knowledge(knowledge_id, category, title, content):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE it_knowledge
            SET category = ?, title = ?, content = ?, updated_at = ?
            WHERE id = ?
        """, (category, title, content, now, knowledge_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_it_knowledge(knowledge_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM it_knowledge WHERE id = ?", (knowledge_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_approved_knowledge_answer(question):
    knowledge_items = get_it_knowledge()
    if not knowledge_items or not question:
        return None

    q = re.sub(r"[^\w\s]", " ", question.lower()).strip()
    words = set(q.split()) - {"what", "is", "how", "to", "the", "a", "an", "i", "can", "my", "me", "do", "in"}

    best_match = None
    best_score = 0

    for item in knowledge_items:
        title = item.get("title", "").lower()
        content = item.get("content", "").lower()
        combined = f"{title} {content}"

        score = sum(1 for w in words if w in combined)
        if title in q or q in title:
            score += 10

        if score > best_score and score >= 2:
            best_score = score
            best_match = item

    if best_match:
        return {
            "answer": f"{best_match['title']}: {best_match['content']}",
            "intent": best_match.get("category", "general"),
            "department": "IT Support",
            "knowledge_id": best_match.get("id")
        }
    return None
