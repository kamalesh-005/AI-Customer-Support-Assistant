# Admin Panel — Integration Instructions

This package adds a fully separate Admin Panel to your existing AI Customer
Support Assistant project **without modifying any of your existing files**,
except for one unavoidable, one-line addition to `app.py` (explained below).

## 1. What's in this package

```
admin/
├── __init__.py      # Blueprint definition
├── routes.py         # All /admin/* routes
└── db.py              # Creates the new "admins" table, seeds a default admin

templates/admin/
├── base_admin.html    # Sidebar layout shared by all admin pages
├── login.html
├── dashboard.html
├── tickets.html
└── ticket_detail.html

static/admin/
└── admin.css           # Admin-only styling (does not affect your existing theme.css)
```

## 2. Copy the files into your project

Copy these three folders into the root of your existing project, merging
them alongside what's already there:

```
AI-Customer-Support-Assistant/
├── app.py                  <- existing, only 2 lines added (step 3)
├── database.py             <- existing, untouched
├── config.py                <- existing, untouched
├── support.db                <- existing, untouched (one new table added automatically)
├── admin/                    <- NEW (copy this whole folder in)
├── templates/
│   ├── ...your existing templates, untouched...
│   └── admin/                <- NEW (copy this whole folder in)
└── static/
    ├── css/theme.css         <- existing, untouched
    └── admin/                 <- NEW (copy this whole folder in)
```

## 3. The one required change to `app.py`

Flask blueprints must be explicitly registered on the app — there's no way
around this from outside `app.py`. Add these two lines near the top of
`app.py`, after `app = Flask(__name__)` is defined:

```python
app = Flask(__name__)
...
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# --- Admin Panel (new) ---
from admin import admin_bp
app.register_blueprint(admin_bp)
```

Nothing else in `app.py` needs to change. All of your existing routes,
imports, and logic stay exactly as they are.

## 4. First run

Start your app as usual:

```
python app.py
```

On first run, the admin module automatically creates a new `admins` table
in your existing `support.db` (no existing table is touched) and seeds one
default admin account:

```
Username: admin
Password: admin123
```

You'll see this printed in your console. **Change this password** — see
the note in `admin/db.py` about where to add a "change password" route if
you want one; it wasn't in the original spec so it's left as an easy
follow-up rather than guessed at.

## 5. Using it

- Admin login: `http://localhost:5000/admin/login`
- Dashboard: `http://localhost:5000/admin/dashboard`
- Ticket management: `http://localhost:5000/admin/tickets`
- Ticket detail: `http://localhost:5000/admin/ticket/<id>`

Admin auth uses a separate session key (`session["admin"]`) from your
regular user auth (`session["user"]`), so being logged in as a regular
user and an admin at the same time in the same browser works fine and
they never interfere with each other.

## 6. Known limitation: "User Name" column

Your current `tickets` table does not store which user created a ticket —
there's no `user_id` or `username` column on it. Because of that, the
admin ticket table shows `N/A` in the "User" column rather than guessing.

If you'd like real per-ticket ownership later, the minimal-impact fix is:

```sql
ALTER TABLE tickets ADD COLUMN created_by TEXT;
```

...and setting `created_by=session["user"]` in the existing `/ticket` POST
route in `app.py`. This is optional and intentionally **not** included
here, since you asked not to change the database structure unless
necessary — showing `N/A` honestly was the necessary-only choice.

## 7. Verified

This was tested end-to-end with Flask's test client against your actual
`support.db`: admin login, dashboard stats, ticket list with filters, ticket
detail + status update, and logout all pass. Only a new `admins` table was
added to the database; `users` and `tickets` schemas are byte-for-byte
unchanged.
