from flask import Flask, render_template, request, redirect
from database import get_connection
from models import create_table

app = Flask(__name__)

# -----------------------------------
# Database Initialization
# -----------------------------------

create_table()

# -----------------------------------
# Constants
# -----------------------------------

MIN_PERCENTAGE = 60
SHORTLIST_SCORE = 70

PREFERRED_DEPARTMENTS = {"cs", "cse", "it"}


# -----------------------------------
# Helper Functions
# -----------------------------------

def calculate_status(department, percentage, backlog):
    """
    Returns candidate eligibility status.
    """

    department = department.strip().lower()

    if backlog.lower() == "yes" or percentage < MIN_PERCENTAGE:
        return "Not Eligible"

    if department in PREFERRED_DEPARTMENTS:
        return "Eligible"

    return "Review Required"


def calculate_final_status(status, score):
    """
    Returns final shortlist status.
    """

    if score >= SHORTLIST_SCORE and status in ("Eligible", "Review Required"):
        return "Shortlisted"

    return "Rejected"


def validate_candidate(name, email, mobile):

    if not name.strip():
        return "Candidate name is required."

    if "@" not in email or "." not in email:
        return "Enter a valid email address."

    if len(mobile) != 10 or not mobile.isdigit():
        return "Mobile number must contain exactly 10 digits."

    return None


def candidate_exists(conn, email, mobile):

    email_exists = conn.execute(
        "SELECT 1 FROM candidates WHERE email=?",
        (email,)
    ).fetchone()

    if email_exists:
        return "Email already exists."

    mobile_exists = conn.execute(
        "SELECT 1 FROM candidates WHERE mobile=?",
        (mobile,)
    ).fetchone()

    if mobile_exists:
        return "Mobile number already exists."

    return None


# -----------------------------------
# Dashboard
# -----------------------------------

@app.route("/")
def home():

    search = request.args.get("search", "").strip()
    eligibility = request.args.get("eligibility", "")
    tech = request.args.get("tech", "")
    shortlisted = request.args.get("shortlisted", "")

    conn = get_connection()

    query = "SELECT * FROM candidates WHERE 1=1"
    params = []

    if search:
        query += " AND (full_name LIKE ? OR email LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if eligibility:
        query += " AND eligibility_status=?"
        params.append(eligibility)

    if tech:
        query += " AND preferred_tech=?"
        params.append(tech)

    if shortlisted == "yes":
        query += " AND final_shortlist_status='Shortlisted'"

    query += " ORDER BY round1_score DESC"

    candidates = conn.execute(query, params).fetchall()

    conn.close()

    return render_template(
        "index.html",
        candidates=candidates,
        search=search,
        eligibility=eligibility,
        tech=tech,
        shortlisted=shortlisted
    )


# -----------------------------------
# Registration Page
# -----------------------------------

@app.route("/register")
def register():

    return render_template("register.html")


# -----------------------------------
# Candidate Registration
# -----------------------------------

@app.route("/add", methods=["POST"])
def add_candidate():

    name = request.form["name"].strip()
    email = request.form["email"].strip().lower()
    mobile = request.form["mobile"].strip()

    department = request.form["department"]

    percentage = float(request.form["percentage"])

    backlog = request.form["backlog"]

    tech = request.form["tech"]

    skills = ", ".join(request.form.getlist("skills"))

    validation_error = validate_candidate(
        name,
        email,
        mobile
    )

    if validation_error:
        return validation_error

    conn = get_connection()

    duplicate_error = candidate_exists(
        conn,
        email,
        mobile
    )

    if duplicate_error:
        conn.close()
        return duplicate_error

    status = calculate_status(
        department,
        percentage,
        backlog
    )

    conn.execute(
        """
        INSERT INTO candidates
        (
            full_name,
            email,
            mobile,
            department,
            percentage,
            active_backlog,
            preferred_tech,
            skills,
            eligibility_status
        )

        VALUES
        (
            ?,?,?,?,?,?,?,?,?
        )
        """,

        (
            name,
            email,
            mobile,
            department,
            percentage,
            backlog,
            tech,
            skills,
            status
        )

    )

    conn.commit()
    conn.close()

    return redirect("/")


# -----------------------------------
# Round 1 Evaluation
# -----------------------------------

@app.route("/score/<int:id>", methods=["POST"])
def score(id):

    print("=" * 60)
    print("FORM:", request.form)

    score = int(request.form["score"])
    print("Score received:", score)

    conn = get_connection()

    candidate = conn.execute(
        "SELECT * FROM candidates WHERE id=?",
        (id,)
    ).fetchone()

    print("Candidate:", candidate["full_name"])
    print("Eligibility:", candidate["eligibility_status"])

    final_status = calculate_final_status(
        candidate["eligibility_status"],
        score
    )

    print("Final status:", final_status)

    conn.execute(
        """
        UPDATE candidates
        SET round1_score=?,
            final_shortlist_status=?
        WHERE id=?
        """,
        (score, final_status, id)
    )

    conn.commit()

    row = conn.execute(
        "SELECT round1_score, final_shortlist_status FROM candidates WHERE id=?",
        (id,)
    ).fetchone()

    print("Saved score:", row["round1_score"])
    print("Saved status:", row["final_shortlist_status"])
    print("=" * 60)

    conn.close()

    return redirect("/")

# -----------------------------------
# Run Application
# -----------------------------------

if __name__ == "__main__":
    app.run(debug=True)