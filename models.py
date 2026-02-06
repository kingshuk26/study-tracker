from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# ---------------- USERS ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    google_id = db.Column(db.String(200))
    telegram_id = db.Column(db.String, nullable=True)
    leetcode = db.Column(db.String, nullable=True)
    gfg = db.Column(db.String, nullable=True)
    linkedin = db.Column(db.String, nullable=True)
    github = db.Column(db.String, nullable=True)
    

# ---------------- SUBJECT ----------------
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


# ---------------- SECTION (⭐ HEADING) ----------------
class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))

    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"))
    

# ---------------- TOPIC ----------------
class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)
    hours = db.Column(db.Float, default=0)

    section_id = db.Column(db.Integer, db.ForeignKey("section.id"))


from datetime import date

class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    date = db.Column(db.Date)

    dsa = db.Column(db.Boolean, default=False)
    aptitude = db.Column(db.Boolean, default=False)
    dev = db.Column(db.Boolean, default=False)
    project = db.Column(db.Boolean, default=False)
    
    notes = db.Column(db.Text, default="")
    


