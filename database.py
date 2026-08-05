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

# Delete all existing sample tickets
cursor.execute("DELETE FROM tickets")


sample_tickets = [

    # Open
    ("Login Issue", "Account", "High", "User cannot login", "Open"),
    ("Payment Failed", "Billing", "Medium", "Payment not processed", "Open"),
    ("Profile Update", "Profile", "Low", "Unable to update profile", "Open"),

    # In Progress
    ("Password Reset", "Account", "High", "Forgot password", "In Progress"),
    ("Bug Report", "Technical", "Medium", "Application crashes", "In Progress"),
    ("Email Verification", "Account", "Low", "OTP not received", "In Progress"),

    # Resolved
    ("Refund Request", "Billing", "High", "Refund completed", "Resolved"),
    ("Account Unlock", "Account", "Medium", "Account unlocked", "Resolved"),
    ("Ticket Update", "Support", "Low", "Issue resolved", "Resolved"),

    # Closed
    ("Feature Request", "General", "Low", "Dark mode added", "Closed"),
    ("Installation Help", "Technical", "Medium", "Software installed", "Closed"),
    ("Chatbot Issue", "AI", "High", "AI response fixed", "Closed"),
]

cursor.executemany("""
INSERT INTO tickets(title, category, priority, description, status)
VALUES (?, ?, ?, ?, ?)
""", sample_tickets)

cursor.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
print(cursor.fetchall())

connection.commit()
connection.close()

print("Database created/updated successfully!")