import os
from pathlib import Path
from datetime import date, datetime, timedelta

from flask import Flask, request, jsonify   # ✅ correct imports
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import UniqueConstraint

# Optional in dev: allow Svelte (5173) to call /api/*
# from flask_cors import CORS

app = Flask(__name__, instance_relative_config=True)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})  # ← enable if not using Vite proxy

# --- Database setup (SQLite under instance/) ---
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(app.instance_path, "habits.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Models ---
class Habit(db.Model):
    __tablename__ = "habits"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created = db.Column(db.Date, nullable=False, default=date.today)
    last_completed = db.Column(db.Date, nullable=True)
    streak = db.Column(db.Integer, nullable=False, default=0)

    completions = db.relationship(
        "Completion", backref="habit", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Habit {self.name}>"

class Completion(db.Model):
    __tablename__ = "completions"
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False)
    done_on = db.Column(db.Date, nullable=False)
    __table_args__ = (UniqueConstraint("habit_id", "done_on", name="uix_habit_day"),)

# --- API ROUTES ONLY ---

@app.get("/api/habits")
def api_habits():
    habits = Habit.query.order_by(Habit.created.desc()).all()
    return jsonify({
        "habits": [
            {
                "id": h.id,
                "name": h.name,
                "streak": h.streak,
                "created": h.created.isoformat(),
                "last_completed": h.last_completed.isoformat() if h.last_completed else None,
                "history": [c.done_on.isoformat() for c in h.completions.order_by(Completion.done_on.asc())]
            } for h in habits
        ]
    })

@app.post("/api/habits")
def api_add_habit():
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return {"error": "name required"}, 400
    h = Habit(name=name)
    db.session.add(h)
    db.session.commit()
    return {"ok": True, "id": h.id}, 201

@app.post("/api/habits/<int:habit_id>/toggle")
def api_toggle(habit_id):
    h = Habit.query.get_or_404(habit_id)
    today = date.today()
    already = Completion.query.filter_by(habit_id=h.id, done_on=today).first()
    if not already:
        db.session.add(Completion(habit_id=h.id, done_on=today))
        yesterday = today - timedelta(days=1)
        had_yesterday = Completion.query.filter_by(habit_id=h.id, done_on=yesterday).first() is not None
        h.streak = (h.streak or 0) + 1 if (h.last_completed == yesterday and had_yesterday) else 1
        h.last_completed = today
        db.session.commit()
    return {"ok": True, "streak": h.streak, "last_completed": h.last_completed.isoformat()}

@app.delete("/api/habits/<int:habit_id>")
def api_delete(habit_id):
    h = Habit.query.get_or_404(habit_id)
    db.session.delete(h)
    db.session.commit()
    return {"ok": True}

@app.get("/api/stats")
def api_stats():
    habits = Habit.query.all()
    total_habits = len(habits)
    total_completions = sum(h.streak or 0 for h in habits)
    longest_streak = max([h.streak or 0 for h in habits], default=0)
    average_streak = round(total_completions / total_habits, 2) if total_habits else 0
    return {
        "total_habits": total_habits,
        "total_completions": total_completions,
        "longest_streak": longest_streak,
        "average_streak": average_streak
    }

@app.get("/api/calendar")
def api_calendar():
    habits = Habit.query.order_by(Habit.id.asc()).all()
    events = []
    palette = ['#FF6B6B','#6BCB77','#4D96FF','#FFD93D','#A66DD4','#00C49A','#FBA834','#FF90BC','#8ACDD7','#BDB2FF']
    for i, h in enumerate(habits):
        color = palette[i % len(palette)]
        for c in h.completions.order_by(Completion.done_on.asc()).all():
            events.append({"title": h.name, "start": c.done_on.isoformat(), "color": color})
    return {"events": events}

#errorhandler 
@app.errorhandler(404)
def not_found(e):
    return {"error": "Not found"}, 404

@app.errorhandler(500)
def server_error(e):
    return {"error": "Server error"}, 500

# health check
@app.get("/")
def health():
    return {"status": "ok"}

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)

