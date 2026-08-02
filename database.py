import sqlite3

connection = sqlite3.connect("support.db")
cursor = connection.cursor()

# ---------------- USERS TABLE ---------------- #

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT,
    password TEXT
)
""")

# ---------------- TICKETS TABLE ---------------- #

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    category TEXT,
    priority TEXT,
    description TEXT,
    status TEXT DEFAULT 'Open'
)
""")

# ---------------- CHATS TABLE ---------------- #

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    user_message TEXT,
    ai_response TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# ---------------- PASSWORD RESET TABLE ---------------- #

cursor.execute("""
CREATE TABLE IF NOT EXISTS password_reset(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    otp TEXT,
    created_time TEXT
)
""")

# ---------------- FEEDBACK TABLE ---------------- #

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    username TEXT,
    rating TEXT
)
""")

# ---------------- ADD ATTACHMENT COLUMN ---------------- #

try:
    cursor.execute("""
    ALTER TABLE tickets
    ADD COLUMN attachment TEXT
    """)
except sqlite3.OperationalError:
    # Column already exists
    pass

connection.commit()
connection.close()

print("Database created/updated successfully!")