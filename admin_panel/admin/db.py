"""
Admin database helper.

Reuses the SAME SQLite file (support.db) that the rest of the app uses.
The ONLY schema change made here is creating a new "admins" table if it
doesn't already exist. No existing table (users, tickets, chats, etc.)
is modified in any way.
"""

import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "support.db"

# Default admin account created automatically on first run.
# CHANGE THIS PASSWORD after your first login (see admin/routes.py
# for where you'd add a "change password" route if you want one later).
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def get_connection():
    """Same pattern used everywhere else in app.py: a fresh sqlite3
    connection per request/operation."""
    return sqlite3.connect(DB_PATH)


def init_admin_table():
    """
    Creates the 'admins' table if it does not already exist, and seeds
    one default admin account if the table is empty. Safe to call every
    time the app starts (idempotent).
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM admins")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute(
            "INSERT INTO admins(username, password_hash) VALUES (?, ?)",
            (DEFAULT_ADMIN_USERNAME, generate_password_hash(DEFAULT_ADMIN_PASSWORD)),
        )
        print(
            f"[admin] Default admin account created -> "
            f"username: '{DEFAULT_ADMIN_USERNAME}'  password: '{DEFAULT_ADMIN_PASSWORD}'"
        )
        print("[admin] Please log in and change this password as soon as possible.")

    connection.commit()
    connection.close()


# Run automatically as soon as the admin package is imported.
init_admin_table()
