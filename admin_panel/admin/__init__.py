"""
Admin Panel Blueprint
======================
This package is completely self-contained and does not modify any of the
existing user-facing routes, templates, or database tables.

It reuses the existing SQLite database (support.db) and only ADDS one new
table ("admins") to store admin login credentials. No existing table is
altered.

To wire this into the main app, only ONE line needs to be added to app.py:

    from admin import admin_bp
    app.register_blueprint(admin_bp)

That's it — see INTEGRATION.md for exact instructions.
"""

from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    # NOTE: no template_folder is set here on purpose. The main Flask app
    # already uses "templates/" as its template root, and our admin
    # templates live at templates/admin/*.html, so render_template()
    # calls like "admin/login.html" resolve correctly against the app's
    # existing Jinja loader without any extra configuration.
    static_folder="../static/admin",
    static_url_path="/admin/static",
)

# Import routes AFTER admin_bp is created to avoid circular imports.
from admin import routes  # noqa: E402,F401

# Ensure the admins table exists (and seed a default admin) on import.
from admin import db as admin_db  # noqa: E402,F401
