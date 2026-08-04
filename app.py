from flask import Flask, jsonify, render_template, request, redirect, send_file, session
import sqlite3
import re
import os
import random
from datetime import datetime
from google import genai
from config import GEMINI_API_KEY
from pdf_export import export_chat_to_pdf
from werkzeug.utils import secure_filename
from flask import session

import database
from config import EMAIL_ADDRESS, EMAIL_PASSWORD

print("Email:", EMAIL_ADDRESS)
print("Password Loaded:", EMAIL_PASSWORD is not None)

import smtplib
from email.mime.text import MIMEText
from config import EMAIL_ADDRESS, EMAIL_PASSWORD

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

client = genai.Client(api_key=GEMINI_API_KEY)


# ---------------- BUILT-IN AI CHATBOT (FALLBACK) ---------------- #

def chatbot_response(message):

    message = message.lower()

    # Greetings
    if any(word in message for word in ["hi", "hello", "hey"]):
        return "Hello! Welcome to AI Customer Support. How can I assist you today?"

    # Password
    elif "password" in message:
        return "If you forgot your password, click the 'Forgot Password' option on the login page."

    # Login
    elif "login" in message:
        return "Please make sure your email and password are correct. If the issue continues, reset your password."

    # Register
    elif "register" in message or "signup" in message:
        return "Click the Register button on the home page and fill in your details."

    # Ticket
    elif "ticket" in message:
        return "You can create a support ticket from the Dashboard. Our support team will review it."

    # Refund
    elif "refund" in message:
        return "Refund requests are generally processed within 3-5 business days."

    # Contact
    elif "contact" in message:
        return "You can contact our support team by creating a support ticket."

    # Thanks
    elif "thank" in message:
        return "You're welcome! Happy to help."

    # Goodbye
    elif "bye" in message:
        return "Thank you for visiting. Have a wonderful day!"

    # Default
    else:
        return (
            "I'm sorry, I couldn't understand your request. "
            "Please create a support ticket if you need further assistance."
        )


# ---------------- GEMINI AI RESPONSE ---------------- #

def generate_ai_response(message, previous_chats):

    system_prompt = f"""
You are SupportBot, a professional AI Customer Support Assistant.

Your responsibilities:
- Greet customers politely.
- Answer customer questions professionally.
- Help users solve technical issues step by step.
- Keep responses short, clear, and friendly.
- Use bullet points or numbered steps whenever helpful.
- If you don't know an answer, say so honestly.
- Never make up information.
- If the issue requires human assistance, politely recommend contacting customer support.

Customer Message:
{message}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=system_prompt
        )

        return response.text

    except Exception as e:
        print("Gemini Error:", e)

        # Fallback to the built-in chatbot if the API call fails
        return chatbot_response(message)


def send_otp_email(receiver_email, otp):

    subject = "AI Customer Support - Email Verification OTP"

    body = f"""
Hello,

Your OTP for AI Customer Support Assistant is:

{otp}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

Thank you,
AI Customer Support Team
"""

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = EMAIL_ADDRESS
    message["To"] = receiver_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)

        return True

    except Exception as e:
        print("Email Error:", e)
        return False


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("support.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:
            session["user"] = user[1]
            return redirect("/dashboard")
        else:
            return "<h2>Invalid Email or Password</h2>"

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    print("Method:", request.method)

    if request.method == "POST":

        print("Inside POST")

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not re.match(email_pattern, email):
            return """
            <script>
                alert("Invalid Email Address!");
                window.history.back();
            </script>
            """

        connection = sqlite3.connect("support.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        existing_user = cursor.fetchone()

        connection.close()

        if existing_user:
            return """
            <script>
                alert("Email is already registered!");
                window.history.back();
            </script>
            """

        otp = str(random.randint(100000, 999999))

        session["pending_user"] = {
            "fullname": fullname,
            "email": email,
            "password": password,
            "otp": otp
        }



        print("Generated OTP:", otp)

        result = send_otp_email(email, otp)
        print("Email sent:", result)

    if result:
        return redirect("/verify_otp")
    else:
        return """
    <script>
        alert("Failed to send OTP. Please try again.");
        window.history.back();
      </script>
       """
    return render_template("register.html")
# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    # Total chats of the logged-in user
    cursor.execute(
        "SELECT COUNT(*) FROM chats WHERE username=?",
        (session["user"],)
    )
    total_chats = cursor.fetchone()[0]

    # Total AI responses
    cursor.execute(
        "SELECT COUNT(ai_response) FROM chats WHERE username=?",
        (session["user"],)
    )
    total_ai_responses = cursor.fetchone()[0]

    # Total tickets
    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0]

    # Ticket statistics
    cursor.execute("""
        SELECT status, COUNT(*)
        FROM tickets
        GROUP BY status
    """)
    ticket_stats = cursor.fetchall()

    # Open Tickets
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'")
    open_count = cursor.fetchone()[0]

    # In Progress Tickets
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status='In Progress'")
    in_progress_count = cursor.fetchone()[0]

    # Resolved Tickets
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status='Resolved'")
    resolved_count = cursor.fetchone()[0]

    # Closed Tickets
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status='Closed'")
    closed_count = cursor.fetchone()[0]

    # Recent tickets
    cursor.execute("""
        SELECT title, priority, status
        FROM tickets
        ORDER BY id DESC
        LIMIT 5
    """)
    recent_tickets = cursor.fetchall()

    # Last chat time
    cursor.execute("""
        SELECT created_at
        FROM chats
        WHERE username=?
        ORDER BY id DESC
        LIMIT 1
    """, (session["user"],))

    last_chat = cursor.fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        username=session["user"],
        total_chats=total_chats,
        total_tickets=total_tickets,
        last_chat=last_chat,
        ticket_stats=ticket_stats,
        recent_tickets=recent_tickets,
        total_ai_responses=total_ai_responses,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        closed_count=closed_count
    )


# ---------------- CREATE TICKET ---------------- #

@app.route("/ticket", methods=["GET", "POST"])
def create_ticket():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        title = request.form["title"]
        category = request.form["category"]
        priority = request.form["priority"]
        description = request.form["description"]

        # File Upload
        attachment = request.files.get("attachment")

        filename = None

        if attachment and attachment.filename != "":
            filename = secure_filename(attachment.filename)
            attachment.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )

        connection = sqlite3.connect("support.db")
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO tickets
            (title, category, priority, description, status, attachment)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            category,
            priority,
            description,
            "Open",
            filename
        ))

        connection.commit()
        connection.close()

        return """
        <script>
            alert("Ticket Created Successfully!");
            window.location='/dashboard';
        </script>
        """

    return render_template("ticket.html")


# ---------------- CHAT ---------------- #

@app.route("/chat", methods=["GET", "POST"])
def chat():

    if "user" not in session:
        return redirect("/login")

    user_message = ""
    ai_reply = ""

    if request.method == "POST":

        user_message = request.form["message"]

        # Connect to database
        connection = sqlite3.connect("support.db")
        cursor = connection.cursor()

        # Fetch last 5 conversations of the logged-in user
        cursor.execute("""
            SELECT user_message, ai_response
            FROM chats
            WHERE username = ?
            ORDER BY id DESC
            LIMIT 5
        """, (session["user"],))

        previous_chats = cursor.fetchall()

        connection.close()

        # Generate exactly one AI response using Gemini,
        # falling back to the built-in chatbot on failure.
        ai_reply = generate_ai_response(user_message, previous_chats)

        connection = sqlite3.connect("support.db")
        cursor = connection.cursor()

        current_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        cursor.execute("""
            INSERT INTO chats(username, user_message, ai_response, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            session["user"],
            user_message,
            ai_reply,
            current_time
        ))

        connection.commit()
        connection.close()

    # -------- LOAD CHAT HISTORY -------- #

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    search = request.args.get("search", "")

    if search:

        cursor.execute("""
            SELECT id, user_message, ai_response, created_at
            FROM chats
            WHERE username=?
            AND (
                user_message LIKE ?
                OR ai_response LIKE ?
            )
            ORDER BY id ASC
        """, (
            session["user"],
            "%" + search + "%",
            "%" + search + "%"
        ))

    else:

        cursor.execute("""
            SELECT id, user_message, ai_response, created_at
            FROM chats
            WHERE username=?
            ORDER BY id ASC
        """, (session["user"],))

    chats = cursor.fetchall()

    connection.close()

    return render_template(
        "chat.html",
        chats=chats,
        user_message=user_message,
        ai_response=ai_reply,
        search=search
    )


# ---------------- CHAT API ---------------- #

@app.route("/chat_api", methods=["POST"])
def chat_api():

    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_message = request.json.get("message")

    # Fetch previous chats
    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_message, ai_response
        FROM chats
        WHERE username = ?
        ORDER BY id DESC
        LIMIT 5
    """, (session["user"],))

    previous_chats = cursor.fetchall()

    connection.close()

    ai_reply = generate_ai_response(user_message, previous_chats)

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    current_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    cursor.execute("""
        INSERT INTO chats(username, user_message, ai_response, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        session["user"],
        user_message,
        ai_reply,
        current_time
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "user_message": user_message,
        "ai_reply": ai_reply,
        "time": current_time
    })


# ---------------- DELETE CHAT ---------------- #

@app.route("/delete_chat/<int:id>")
def delete_chat(id):

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM chats
        WHERE id=? AND username=?
    """, (id, session["user"]))

    connection.commit()
    connection.close()

    return redirect("/chat")


# ---------------- CLEAR CHAT HISTORY ---------------- #

@app.route("/clear_chat")
def clear_chat():

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM chats
        WHERE username=?
    """, (session["user"],))

    connection.commit()
    connection.close()

    return redirect("/chat")


# ---------------- VIEW TICKETS ---------------- #

@app.route("/view_tickets")
def view_tickets():

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    status = request.args.get("status", "All")
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "Newest")

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    # Status Filter
    if status != "All":
        query += " AND status=?"
        params.append(status)

    # Search
    if search:
        query += " AND (title LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    # Sorting
    if sort == "Newest":
        query += " ORDER BY id DESC"

    elif sort == "Oldest":
        query += " ORDER BY id ASC"

    elif sort == "Priority":
        query += """
        ORDER BY
        CASE priority
            WHEN 'High' THEN 1
            WHEN 'Medium' THEN 2
            WHEN 'Low' THEN 3
        END
        """

    elif sort == "Status":
        query += " ORDER BY status"

    # Count total tickets
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total_tickets = cursor.fetchone()[0]

    # Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    cursor.execute(query, params)
    tickets = cursor.fetchall()

    connection.close()

    total_pages = (total_tickets + per_page - 1) // per_page

    return render_template(
        "view_tickets.html",
        tickets=tickets,
        status=status,
        search=search,
        sort=sort,
        page=page,
        total_pages=total_pages
    )


# ---------------- EDIT TICKET ---------------- #

@app.route("/edit_ticket/<int:id>", methods=["GET", "POST"])
def edit_ticket(id):

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    if request.method == "POST":

        title = request.form["title"]
        category = request.form["category"]
        priority = request.form["priority"]
        description = request.form["description"]

        cursor.execute("""
            UPDATE tickets
            SET title=?, category=?, priority=?, description=?
            WHERE id=?
        """, (title, category, priority, description, id))

        connection.commit()
        connection.close()

        return redirect("/view_tickets")

    cursor.execute(
        "SELECT * FROM tickets WHERE id=?",
        (id,)
    )

    ticket = cursor.fetchone()

    connection.close()

    return render_template(
        "edit_ticket.html",
        ticket=ticket
    )


# ---------------- DELETE TICKET ---------------- #

@app.route("/delete_ticket/<int:id>")
def delete_ticket(id):

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM tickets WHERE id=?",
        (id,)
    )

    connection.commit()
    connection.close()

    return redirect("/view_tickets")


# ---------------- SEND OTP ---------------- #

@app.route("/send_otp", methods=["POST"])
def send_otp():

    email = request.form["email"]

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    if not user:
        connection.close()

        return """
        <script>
            alert("Email not registered!");
            window.history.back();
        </script>
        """

    otp = str(random.randint(100000, 999999))

    cursor.execute(
        """
        INSERT INTO password_reset(email, otp, created_time)
        VALUES (?, ?, datetime('now'))
        """,
        (email, otp)
    )

    connection.commit()
    connection.close()

    return f"""
    <script>
        alert("Your OTP is: {otp}");
        window.history.back();
    </script>
    """


# ---------------- PROFILE ---------------- #

@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE fullname=?",
        (session["user"],)
    )

    user = cursor.fetchone()

    connection.close()

    return render_template(
        "profile.html",
        user=user
    )


# ---------------- EDIT PROFILE ---------------- #

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE fullname=?",
        (session["user"],)
    )

    user = cursor.fetchone()

    if request.method == "POST":

        fullname = request.form["fullname"]

        cursor.execute(
            """
            UPDATE users
            SET fullname=?
            WHERE id=?
            """,
            (fullname, user[0])
        )

        connection.commit()

        # Update session with new name
        session["user"] = fullname

        connection.close()

        return redirect("/profile")

    connection.close()

    return render_template(
        "edit_profile.html",
        user=user
    )


# ---------------- FEEDBACK ---------------- #

@app.route("/feedback/<int:chat_id>/<rating>")
def feedback(chat_id, rating):

    if "user" not in session:
        return redirect("/login")

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO feedback(chat_id, username, rating)
        VALUES (?, ?, ?)
    """, (
        chat_id,
        session["user"],
        rating
    ))

    connection.commit()
    connection.close()

    return redirect("/chat")


# ---------------- EXPORT CHAT PDF ---------------- #

@app.route("/download_chat_pdf")
def download_chat_pdf():

    if "user" not in session:
        return redirect("/login")

    filename = export_chat_to_pdf(session["user"])

    return send_file(
        filename,
        as_attachment=True
    )


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/test_email")
def test_email():

    otp = "123456"

    if send_otp_email("YOUR_EMAIL@gmail.com", otp):
        return "Email sent successfully!"

    return "Failed to send email."


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)