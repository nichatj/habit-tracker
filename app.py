from flask import Flask, render_template, request, redirect
import json
import os
from datetime import date
import random

app = Flask(__name__)

DATA_FILE = 'habit_data.json'

def load_habits():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_habits(habits):
    with open(DATA_FILE, 'w') as f:
        json.dump(habits, f, indent=4)

@app.route('/')
def index():
    habits = load_habits()
    return render_template('index.html', habits=habits)

@app.route('/add', methods=['POST'])
def add():
    name = request.form['habit_name']
    habits = load_habits()
    habits.append({
        'name': name,
        'created': str(date.today()),
        'last_completed': None,
        'streak': 0,
        'history': []
    })
    save_habits(habits)
    return redirect('/')

@app.route('/complete/<int:index>')
def complete(index):
    habits = load_habits()
    today = str(date.today())
    if today not in habits[index]["history"]:
        habits[index]["history"].append(today)
        habits[index]["last_completed"] = today
        habits[index]["streak"] += 1  # Simple version
    save_habits(habits)
    return redirect('/')

@app.route('/delete/<int:index>')
def delete(index):
    habits = load_habits()
    if 0 <= index < len(habits):
        habits.pop(index)
        save_habits(habits)
    return redirect('/')

@app.route('/stats')
def stats():
    with open('habit_data.json', 'r') as f:
        habits = json.load(f)

    total_habits = len(habits)
    total_completions = sum(h['streak'] for h in habits)
    longest_streak = max((h['streak'] for h in habits), default=0)
    average_streak = round(total_completions / total_habits, 2) if total_habits > 0 else 0

    # Extract data for chart
    habit_names = [h['name'] for h in habits]
    habit_streaks = [h['streak'] for h in habits]

    return render_template(
        'stats.html',
        total_habits=total_habits,
        total_completions=total_completions,
        longest_streak=longest_streak,
        average_streak=average_streak,
        habit_names=habit_names,
        habit_streaks=habit_streaks
    )


@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit(index):
    habits = load_habits()

    if request.method == 'POST':
        new_name = request.form['new_name']
        new_streak = int(request.form['new_streak'])
        new_created = request.form['new_created']
        new_history_raw = request.form['new_history']

        # Sanitize history input
        new_history = [d.strip() for d in new_history_raw.split(',') if d.strip()]

        # Update the habit
        habits[index]['name'] = new_name
        habits[index]['streak'] = new_streak
        habits[index]['created'] = new_created
        habits[index]['history'] = new_history

        save_habits(habits)
        return redirect('/')

    habit = habits[index]
    return render_template('edit.html', habit=habit, index=index)


@app.route('/calendar')
def calendar_view():
    with open('habit_data.json', 'r') as f:
        habits = json.load(f)

    color_palette = [
        '#FF6B6B', '#6BCB77', '#4D96FF', '#FFD93D', '#A66DD4',
        '#00C49A', '#FBA834', '#FF90BC', '#8ACDD7', '#BDB2FF'
    ]

    events = []
    for i, habit in enumerate(habits):
        name = habit["name"]
        color = color_palette[i % len(color_palette)]  # Assign color based on index
        for d in habit.get("history", []):
            events.append({
                "title": name,
                "start": d,
                "color": color  # 👈 Add the color to each event
            })

    return render_template("calendar.html", events=events)

if __name__ == '__main__':
    app.run(debug=True)
