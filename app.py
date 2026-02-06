from flask import Flask, render_template, request, redirect
from models import db, User, Subject, Section, Topic, DailyLog
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from authlib.integrations.flask_client import OAuth
from datetime import date, timedelta
import threading
from telegram_bot import run_bot
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


db.init_app(app)


# ---------------- LOGIN SETUP ----------------
login_manager = LoginManager(app)
login_manager.login_view = "login"

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================================================
# 🔥 LANDING PAGE (NEW)
# =====================================================
@app.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect("/dashboard")
    return render_template("landing.html")


# ---------------- LOGIN ROUTES ----------------
@app.route("/login")
def login():
    return google.authorize_redirect("http://127.0.0.1:5000/authorize")


@app.route("/authorize")
def authorize():
    token = google.authorize_access_token()
    user_info = token["userinfo"]

    user = User.query.filter_by(email=user_info["email"]).first()

    if not user:
        user = User(
            name=user_info["name"],
            email=user_info["email"],
            google_id=user_info["sub"]
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)

    # 🔥 redirect to dashboard (FIXED)
    return redirect("/dashboard")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ---------------- PROFILE ----------------
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")



# =====================================================
# 🔥 DASHBOARD (MOVED FROM / TO /dashboard)
# =====================================================
@app.route("/dashboard")
@login_required
def dashboard():

    selected_date = request.args.get("date")

    if selected_date:
        selected_date = date.fromisoformat(selected_date)
    else:
        selected_date = date.today()

    day = DailyLog.query.filter_by(
        user_id=current_user.id,
        date=selected_date
    ).first()

    heatmap = []

    for i in range(35):
        d = date.today() - timedelta(days=34 - i)

        log = DailyLog.query.filter_by(
            user_id=current_user.id,
            date=d
        ).first()

        level = 0
        if log:
            level = sum([log.dsa, log.aptitude, log.dev, log.project])

        heatmap.append({"date": d, "level": level})

    # ---------------- STREAK ----------------
    streak = 0
    today = date.today()

    for i in range(365):
        d = today - timedelta(days=i)

        log = DailyLog.query.filter_by(
            user_id=current_user.id,
            date=d
        ).first()

        if log and (log.dsa or log.aptitude or log.dev or log.project):
            streak += 1
        else:
            break

    # ---------------- ANALYTICS ----------------
    logs = DailyLog.query.filter_by(user_id=current_user.id).all()

    subject_stats = {
        "DSA": 0,
        "Aptitude": 0,
        "Development": 0,
        "Project": 0
    }

    weekly = [0] * 7

    for log in logs:
        count = sum([log.dsa, log.aptitude, log.dev, log.project])

        if log.dsa: subject_stats["DSA"] += 1
        if log.aptitude: subject_stats["Aptitude"] += 1
        if log.dev: subject_stats["Development"] += 1
        if log.project: subject_stats["Project"] += 1

        diff = (date.today() - log.date).days
        if diff < 7:
            weekly[6 - diff] = count

    return render_template(
        "dashboard.html",
        streak=streak,
        selected_date=selected_date,
        prev_date=selected_date - timedelta(days=1),
        next_date=selected_date + timedelta(days=1),
        day=day,
        heatmap=heatmap,
        subjects=Subject.query.filter_by(user_id=current_user.id).all(),
        weekly=weekly,
        subject_stats=subject_stats
    )


# ---------------- REMINDERS ----------------
TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_reminders():

    with app.app_context():

        users = User.query.all()

        for user in users:

            if not user.telegram_id:
                continue

            today_log = DailyLog.query.filter_by(
                user_id=user.id,
                date=date.today()
            ).first()

            if not today_log:

                requests.get(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    params={
                        "chat_id": user.telegram_id,
                        "text": "🔥 StudyOS Reminder\nAaj ka tracker fill nahi kiya bhai 😤"
                    }
                )


# ---------------- ADD SUBJECT ----------------
@app.route("/add-subject", methods=["POST"])
@login_required
def add_subject():
    name = request.form["name"]

    subject = Subject(name=name, user_id=current_user.id)
    db.session.add(subject)
    db.session.commit()

    return redirect("/dashboard")


# ---------------- SAVE DAY ----------------
@app.route("/save-day", methods=["POST"])
@login_required
def save_day():

    d = date.fromisoformat(request.form["date"])

    log = DailyLog.query.filter_by(
        user_id=current_user.id,
        date=d
    ).first()

    if not log:
        log = DailyLog(user_id=current_user.id, date=d)
        db.session.add(log)

    log.dsa = "dsa" in request.form
    log.aptitude = "aptitude" in request.form
    log.dev = "dev" in request.form
    log.project = "project" in request.form

    db.session.commit()

    return redirect(f"/dashboard?date={d}")


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    threading.Thread(target=run_bot, args=(app,), daemon=True).start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_reminders, 'cron', hour=21, minute=0)
    scheduler.start()

    app.run(debug=True, use_reloader=False)
