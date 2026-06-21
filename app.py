@@ -0,0 +1,282 @@
"""
app.py
Travel Budget Planner — Flask Backend
Course: 21CSC205P Database Management Systems
Authors: Pratyush V (RA2311026010977) & Fatin Ahmed (RA2311026010989)
Guide: Dr. Krunal Dhanraj Randive
SRM Institute of Science and Technology, Kattankulathur
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import get_db_connection
from functools import wraps

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_random_string"


# ── Helper: Login Required Decorator ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("🔒 Please log in first.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ── Home ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Register ──────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Check if username already exists
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("⚠ Username already exists. Please choose a different one.", "warning")
            conn.close()
            return render_template("register.html")

        # Insert new user
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
        conn.close()
        flash("✅ Registered! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ── Login ─────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["userId"]
            session["username"] = user["username"]
            flash(f"🌍 Welcome, {user['username']}!", "success")
            return redirect(url_for("recommend"))
        flash("❌ Invalid credentials. Please try again.", "danger")

    return render_template("login.html")


# ── Logout ────────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    session.clear()
    flash("🔓 Logged out.", "info")
    return redirect(url_for("index"))


# ── Profile ───────────────────────────────────────────────────────────────────

@app.route("/profile")
@login_required
def profile():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    user_id = session["user_id"]

    cur.execute(
        """
        SELECT p.firstName, p.lastName, p.dateOfBirth,
               p.preferredCurrency, uc.phone, uc.address
        FROM profile p
        LEFT JOIN user_contact uc ON p.userId = uc.contactId
        WHERE p.userId = %s
        """,
        (user_id,)
    )
    profile_data = cur.fetchone()
    conn.close()
    return render_template("profile.html", profile=profile_data)


# ── Plan Trip / Recommend ─────────────────────────────────────────────────────

@app.route("/recommend", methods=["GET", "POST"])
@login_required
def recommend():
    recs = {}

    if request.method == "POST":
        dest = request.form["destination"].strip()

        try:
            total_budget = float(request.form["budget"])
        except ValueError:
            flash("⚠ Invalid budget format.", "danger")
            return render_template("recommend.html")

        selected = request.form.getlist("categories")

        if not selected:
            flash("⚠ Please select at least one category.", "warning")
            return render_template("recommend.html")

        # Split budget equally among selected categories
        per_category_budget = total_budget / len(selected)

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        if "transport" in selected:
            cur.execute(
                """
                SELECT
                    t.price,
                    t.departureDateTime,
                    t.arrivalDateTime,
                    l1.locationName AS departureLocation,
                    l2.locationName AS destinationLocation,
                    tt.transportType
                FROM transport t
                JOIN location l1 ON t.departureId = l1.locationId
                JOIN location l2 ON t.destinationId = l2.locationId
                JOIN transporttype tt ON t.transportTypeId = tt.transportTypeId
                WHERE t.price <= %s
                  AND t.destinationId = (
                      SELECT locationId FROM location WHERE locationName = %s
                  )
                ORDER BY t.price ASC
                LIMIT 5
                """,
                (per_category_budget, dest)
            )
            recs["transport"] = cur.fetchall()

        if "accommodation" in selected:
            cur.execute(
                """
                SELECT name, pricePerNight, location, availableRooms
                FROM accommodation
                WHERE pricePerNight <= %s
                  AND location = %s
                ORDER BY pricePerNight ASC
                LIMIT 5
                """,
                (per_category_budget, dest)
            )
            recs["accommodation"] = cur.fetchall()

        if "activity" in selected:
            cur.execute(
                """
                SELECT name, price, location, date, time
                FROM activity
                WHERE price <= %s
                  AND location = %s
                ORDER BY price ASC
                LIMIT 5
                """,
                (per_category_budget, dest)
            )
            recs["activity"] = cur.fetchall()

        conn.close()
        return render_template("recommend.html", recommendations=recs)

    return render_template("recommend.html", recommendations=recs)


# ── Accommodations ────────────────────────────────────────────────────────────

@app.route("/accommodation")
@login_required
def show_accommodation():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM accommodation")
    data = cur.fetchall()
    conn.close()
    return render_template("accommodation.html", accommodations=data)


# ── Activities ────────────────────────────────────────────────────────────────

@app.route("/activity")
@login_required
def show_activity():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM activity")
    data = cur.fetchall()
    conn.close()
    return render_template("activity.html", activities=data)


# ── Transport ─────────────────────────────────────────────────────────────────

@app.route("/transport")
@login_required
def show_transport():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT
            t.transportId,
            tt.transportType,
            l1.locationName AS departure,
            l2.locationName AS destination,
            t.departureDateTime,
            t.arrivalDateTime,
            t.price,
            t.availableSeats
        FROM transport t
        JOIN transporttype tt ON t.transportTypeId = tt.transportTypeId
        JOIN location l1 ON t.departureId = l1.locationId
        JOIN location l2 ON t.destinationId = l2.locationId
        ORDER BY t.transportId
        """
    )
    transports = cur.fetchall()
    conn.close()
    return render_template("transport.html", transports=transports)


# ── Booking ───────────────────────────────────────────────────────────────────

@app.route("/booking")
@login_required
def show_booking():
    return render_template("booking.html")


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
