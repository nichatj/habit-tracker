import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from datetime import date, datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import UniqueConstraint

app = Flask(__name__, instance_relative_config=True)

# --- Database setup (SQLite file in project root) ---
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
        "Completion",
        backref="habit",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Habit {self.name}>"

class Completion(db.Model):
    __tablename__ = "completions"
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False)
    done_on = db.Column(db.Date, nullable=False)

    __table_args__ = (
        UniqueConstraint("habit_id", "done_on", name="uix_habit_day"),
    )

# --- Routes ---
@app.route("/")
def index():
    habits = Habit.query.order_by(Habit.created.desc()).all()
    return render_template("index.html", habits=[{
        "id": h.id,
        "name": h.name,
        "created": h.created.isoformat(),
        "last_completed": h.last_completed.isoformat() if h.last_completed else None,
        "streak": h.streak,
        "history": [c.done_on.isoformat() for c in h.completions.order_by(Completion.done_on.asc()).all()]
    } for h in habits])

@app.route("/add", methods=["POST"])
def add():
    name = request.form["habit_name"].strip()
    if name:
        h = Habit(name=name)
        db.session.add(h)
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/complete/<int:habit_id>")
def complete(habit_id):
    h = Habit.query.get_or_404(habit_id)
    today = date.today()

    # already completed today? do nothing
    already = Completion.query.filter_by(habit_id=h.id, done_on=today).first()
    if not already:
        db.session.add(Completion(habit_id=h.id, done_on=today))

        # update streak
        yesterday = today - timedelta(days=1)
        had_yesterday = Completion.query.filter_by(habit_id=h.id, done_on=yesterday).first() is not None
        if h.last_completed == yesterday and had_yesterday:
            h.streak = (h.streak or 0) + 1
        else:
            h.streak = 1
        h.last_completed = today

        db.session.commit()

    return redirect(url_for("index"))

@app.route("/delete/<int:habit_id>")
def delete(habit_id):
    h = Habit.query.get_or_404(habit_id)
    db.session.delete(h)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/stats")
def stats():
    habits = Habit.query.all()
    total_habits = len(habits)
    total_completions = sum(h.streak or 0 for h in habits)
    longest_streak = max([h.streak or 0 for h in habits], default=0)
    average_streak = round(total_completions / total_habits, 2) if total_habits > 0 else 0

    habit_names = [h.name for h in habits]
    habit_streaks = [h.streak or 0 for h in habits]

    return render_template(
        "stats.html",
        total_habits=total_habits,
        total_completions=total_completions,
        longest_streak=longest_streak,
        average_streak=average_streak,
        habit_names=habit_names,
        habit_streaks=habit_streaks
    )

@app.route("/edit/<int:habit_id>", methods=["GET", "POST"])
def edit(habit_id):
    h = Habit.query.get_or_404(habit_id)

    if request.method == "POST":
        new_name = request.form["new_name"].strip()
        new_streak = int(request.form["new_streak"])
        new_created_str = request.form["new_created"].strip()
        new_history_raw = request.form["new_history"].strip()

        # update basic fields
        h.name = new_name or h.name
        try:
            h.created = datetime.strptime(new_created_str, "%Y-%m-%d").date()
        except Exception:
            pass

        # accept commas OR newlines for history
        parts = [p.strip() for p in new_history_raw.replace("\n", ",").split(",") if p.strip()]
        parsed_dates = set()
        for d in parts:
            try:
                parsed_dates.add(datetime.strptime(d, "%Y-%m-%d").date())
            except Exception:
                continue

        # compare to current DB history
        existing_dates = {c.done_on for c in h.completions.all()}
        history_changed = parsed_dates != existing_dates

        if history_changed:
            # replace completions to match parsed_dates
            Completion.query.filter_by(habit_id=h.id).delete()
            for dt in sorted(parsed_dates):
                db.session.add(Completion(habit_id=h.id, done_on=dt))

            # recompute streak + last_completed from history
            all_dates = sorted(parsed_dates)
            if all_dates:
                streak = 1
                for i in range(len(all_dates) - 1, 0, -1):
                    if (all_dates[i] - all_dates[i - 1]).days == 1:
                        streak += 1
                    else:
                        break
                h.streak = streak
                h.last_completed = all_dates[-1]
            else:
                h.streak = 0
                h.last_completed = None
        else:
            # keep the user-entered streak if history didn't change
            h.streak = new_streak

        db.session.commit()
        return redirect(url_for("index"))

    habit_dict = {
        "id": h.id,
        "name": h.name,
        "streak": h.streak or 0,
        "created": h.created.isoformat(),
        "history": [c.done_on.isoformat() for c in h.completions.order_by(Completion.done_on.asc()).all()]
    }
    return render_template("edit.html", habit=habit_dict, index=h.id)

@app.route("/calendar")
def calendar_view():
    habits = Habit.query.order_by(Habit.id.asc()).all()

    color_palette = [
        '#FF6B6B', '#6BCB77', '#4D96FF', '#FFD93D', '#A66DD4',
        '#00C49A', '#FBA834', '#FF90BC', '#8ACDD7', '#BDB2FF'
    ]

    events = []
    for i, h in enumerate(habits):
        color = color_palette[i % len(color_palette)]
        for c in h.completions.order_by(Completion.done_on.asc()).all():
            events.append({
                "title": h.name,
                "start": c.done_on.isoformat(),
                "color": color
            })

    return render_template("calendar.html", events=events)

if __name__ == "__main__":
    app.run(debug=True)
