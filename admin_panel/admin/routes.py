"""
Admin Panel Routes

All routes are prefixed with /admin (set on the blueprint itself), and are
completely separate from the existing user-facing routes in app.py.

Ticket rows from the existing schema are:
    (id, title, category, priority, description, status, attachment)

NOTE: The existing "tickets" table has no column linking a ticket to the
user who created it, so there is no reliable "User Name" to display per
ticket without a schema change. We surface this honestly in the UI as
"N/A" rather than guessing. If you want real per-ticket ownership, the
minimal-impact fix would be adding a nullable `created_by` TEXT column to
tickets (a new column, not a change to any existing one) and setting it
in the existing /ticket POST route in app.py. That's optional and left
out here per your instruction not to change the DB unless necessary.
"""

from functools import wraps
from werkzeug.security import check_password_hash

from flask import render_template, request, redirect, session, url_for

from admin import admin_bp
from admin.db import get_connection

VALID_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]


def admin_login_required(view_func):
    """Decorator that protects admin routes using a SEPARATE session key
    ("admin") from the one the regular user-side login uses ("user"), so
    the two auth systems never collide."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin.admin_login"))
        return view_func(*args, **kwargs)

    return wrapped


# ---------------- ADMIN LOGIN ---------------- #

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, username, password_hash FROM admins WHERE username=?",
            (username,),
        )
        admin_row = cursor.fetchone()
        connection.close()

        if admin_row and check_password_hash(admin_row[2], password):
            session["admin"] = admin_row[1]
            return redirect(url_for("admin.admin_dashboard"))

        return render_template(
            "admin/login.html", error="Invalid username or password"
        )

    return render_template("admin/login.html")


@admin_bp.route("/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin.admin_login"))


# ---------------- ADMIN DASHBOARD ---------------- #

@admin_bp.route("/dashboard")
@admin_login_required
def admin_dashboard():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0]

    stats = {}
    for status in VALID_STATUSES:
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status=?", (status,))
        stats[status] = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT id, title, category, priority, status
        FROM tickets
        ORDER BY id DESC
        LIMIT 5
        """
    )
    recent_tickets = cursor.fetchall()

    connection.close()

    return render_template(
        "admin/dashboard.html",
        admin_username=session["admin"],
        total_tickets=total_tickets,
        stats=stats,
        recent_tickets=recent_tickets,
    )


# ---------------- TICKET LIST / MANAGEMENT ---------------- #

@admin_bp.route("/tickets")
@admin_login_required
def admin_tickets():
    connection = get_connection()
    cursor = connection.cursor()

    status = request.args.get("status", "All")
    search = request.args.get("search", "").strip()

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if status != "All":
        query += " AND status=?"
        params.append(status)

    if search:
        query += " AND (title LIKE ? OR category LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    tickets = cursor.fetchall()

    connection.close()

    return render_template(
        "admin/tickets.html",
        tickets=tickets,
        status=status,
        search=search,
        statuses=VALID_STATUSES,
        admin_username=session["admin"],
    )


# ---------------- TICKET DETAIL + STATUS UPDATE ---------------- #

@admin_bp.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
@admin_login_required
def admin_ticket_detail(ticket_id):
    connection = get_connection()
    cursor = connection.cursor()

    if request.method == "POST":
        new_status = request.form.get("status")
        if new_status in VALID_STATUSES:
            cursor.execute(
                "UPDATE tickets SET status=? WHERE id=?", (new_status, ticket_id)
            )
            connection.commit()

    cursor.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
    ticket = cursor.fetchone()
    connection.close()

    if not ticket:
        return redirect(url_for("admin.admin_tickets"))

    return render_template(
        "admin/ticket_detail.html",
        ticket=ticket,
        statuses=VALID_STATUSES,
        admin_username=session["admin"],
    )


# ---------------- QUICK STATUS UPDATE (dropdown from table row) ------- #

@admin_bp.route("/ticket/<int:ticket_id>/status", methods=["POST"])
@admin_login_required
def admin_update_status(ticket_id):
    new_status = request.form.get("status")

    if new_status in VALID_STATUSES:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE tickets SET status=? WHERE id=?", (new_status, ticket_id)
        )
        connection.commit()
        connection.close()

    return redirect(request.referrer or url_for("admin.admin_tickets"))


# ---------------- RESOLVE SHORTCUT ---------------- #

@admin_bp.route("/ticket/<int:ticket_id>/resolve")
@admin_login_required
def admin_resolve_ticket(ticket_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE tickets SET status='Resolved' WHERE id=?", (ticket_id,))
    connection.commit()
    connection.close()
    return redirect(request.referrer or url_for("admin.admin_tickets"))


# ---------------- DELETE TICKET (optional, per spec) ---------------- #

@admin_bp.route("/ticket/<int:ticket_id>/delete")
@admin_login_required
def admin_delete_ticket(ticket_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM tickets WHERE id=?", (ticket_id,))
    connection.commit()
    connection.close()
    return redirect(url_for("admin.admin_tickets"))
