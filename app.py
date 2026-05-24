from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

REGISTRATION_KEY = "company123"

app = Flask(__name__)
app.secret_key = "secret_key"

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# User Model
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20), default="user")  # admin or user


# -----------------------------
# Project Model
# -----------------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    progress = db.Column(db.String(100))
    created_by = db.Column(db.String(100))


# -----------------------------
# Create Database
# -----------------------------
with app.app_context():
    db.create_all()

    # Create Admin User if not exists
    admin = User.query.filter_by(username="admin").first()

    if not admin:
        admin_user = User(
            username="admin",
            password="password",
            role="admin"
        )

        db.session.add(admin_user)
        db.session.commit()


# -----------------------------
# Login Route
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            session["user"] = user.username
            session["role"] = user.role

            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    projects = Project.query.all()

    return render_template(
        "dashboard.html",
        projects=projects,
        current_user=session["user"],
        role=session["role"]
    )


# -----------------------------
# Create Project
# -----------------------------
@app.route("/create", methods=["GET", "POST"])
def create_project():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        progress = request.form["progress"]

        new_project = Project(
            title=title,
            description=description,
            progress=progress,
            created_by=session["user"]
        )

        db.session.add(new_project)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("create_project.html")


# -----------------------------
# Edit Project
# -----------------------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_project(id):

    if "user" not in session:
        return redirect(url_for("login"))

    project = Project.query.get_or_404(id)

    # Permission Check
    if (
        project.created_by != session["user"]
        and session["role"] != "admin"
    ):
        return "Access Denied"

    if request.method == "POST":

        project.title = request.form["title"]
        project.description = request.form["description"]
        project.progress = request.form["progress"]

        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_project.html",
        project=project
    )


# -----------------------------
# Delete Project
# -----------------------------
@app.route("/delete/<int:id>")
def delete_project(id):

    if "user" not in session:
        return redirect(url_for("login"))

    project = Project.query.get_or_404(id)

    if (
        project.created_by != session["user"]
        and session["role"] != "admin"
    ):
        return "Access Denied"

    db.session.delete(project)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        reg_key = request.form["reg_key"]

        # Check registration key
        if reg_key != REGISTRATION_KEY:
            error = "Invalid Registration Key"
            return render_template(
                "register.html",
                error=error
            )

        # Check existing user
        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            error = "Username already exists"

            return render_template(
                "register.html",
                error=error
            )

        # Create normal user
        new_user = User(
            username=username,
            password=password,
            role="user"
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")
# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)