import os
from pathlib import Path
from datetime import date, datetime, timedelta

from flask import Flask, request, jsonify  
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

#edit habit

def _recompute_from_history(h: Habit):
    dates = [c.done_on for c in h.completions.order_by(Completion.done_on.asc()).all()]
    if not dates:
        h.streak = 0
        h.last_completed = None
        return
    h.last_completed = dates[-1]
    # trailing streak ending at last_completed
    streak = 1
    i = len(dates) - 1
    while i > 0 and (dates[i] - dates[i - 1]).days == 1:
        streak += 1
        i -= 1
    h.streak = streak

def _parse_dates(maybe_list):
    out = set()
    if not maybe_list:
        return out
    for x in maybe_list:
        try:
            out.add(datetime.strptime(x.strip(), "%Y-%m-%d").date())
        except Exception:
            pass
    return out

@app.patch("/api/habits/<int:habit_id>")
def api_update_habit(habit_id):
    h = Habit.query.get_or_404(habit_id)
    data = request.json or {}
    history_changed = False

    # name
    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return {"error": "name cannot be empty"}, 400
        h.name = new_name

    # created (YYYY-MM-DD)
    if "created" in data:
        try:
            h.created = datetime.strptime((data["created"] or "").strip(), "%Y-%m-%d").date()
        except Exception:
            return {"error": "invalid created date"}, 400

    # Replace entire history (array of 'YYYY-MM-DD')
    if "history" in data and isinstance(data["history"], list):
        new_dates = sorted(_parse_dates(data["history"]))
        Completion.query.filter_by(habit_id=h.id).delete()
        for d in new_dates:
            db.session.add(Completion(habit_id=h.id, done_on=d))
        history_changed = True

    # Or patch-like operations
    add_dates = _parse_dates(data.get("add_dates"))
    remove_dates = _parse_dates(data.get("remove_dates"))
    if add_dates or remove_dates:
        # add
        for d in add_dates:
            exists = Completion.query.filter_by(habit_id=h.id, done_on=d).first()
            if not exists:
                db.session.add(Completion(habit_id=h.id, done_on=d))
        # remove
        if remove_dates:
            Completion.query.filter(
                Completion.habit_id == h.id,
                Completion.done_on.in_(list(remove_dates))
            ).delete(synchronize_session=False)
        history_changed = True

    # Recompute streak/last_completed when history changed
    if history_changed:
        _recompute_from_history(h)
    else:
        # allow manual streak override only if history not changed
        if "streak" in data:
            try:
                h.streak = int(data["streak"])
            except Exception:
                return {"error": "invalid streak"}, 400

    db.session.commit()
    return {
        "ok": True,
        "habit": {
            "id": h.id,
            "name": h.name,
            "streak": h.streak,
            "created": h.created.isoformat(),
            "last_completed": h.last_completed.isoformat() if h.last_completed else None,
            "history": [c.done_on.isoformat() for c in h.completions.order_by(Completion.done_on.asc())]
        }
    }

@app.post("/api/habits/<int:habit_id>/toggle-date")
def api_toggle_date(habit_id):
    h = Habit.query.get_or_404(habit_id)
    ds = (request.json or {}).get("date", "")
    try:
        d = datetime.strptime(ds.strip(), "%Y-%m-%d").date()
    except Exception:
        return {"error": "invalid date"}, 400

    existing = Completion.query.filter_by(habit_id=h.id, done_on=d).first()
    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Completion(habit_id=h.id, done_on=d))

    _recompute_from_history(h)
    db.session.commit()
    return {"ok": True, "streak": h.streak,
            "last_completed": h.last_completed.isoformat() if h.last_completed else None}

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

