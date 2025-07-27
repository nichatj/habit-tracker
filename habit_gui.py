import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os
from datetime import date, datetime, timedelta
from habit_tracker import load_habits, save_habits, add_habit, delete_habit, mark_completed


DATA_FILE = 'habit_data.json'

def load_habits():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_habits(habits):
    with open(DATA_FILE, 'w') as f:
        json.dump(habits, f, indent=4)

def add_habit():
    name = simpledialog.askstring("Add Habit", "Enter new habit name:")
    if name:
        habits = load_habits()
        habits.append({
            'name': name,
            'created': str(date.today()),
            'last_completed': None,
            'streak': 0
        })
        save_habits(habits)
        refresh_listbox()

def mark_completed():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("No selection", "Select a habit to mark completed.")
        return

    idx = selected[0]
    habits = load_habits()
    today = date.today()
    habit = habits[idx]

    if habit['last_completed'] == str(today):
        messagebox.showinfo("Already done", f"'{habit['name']}' already marked as done today.")
        return

    if habit['last_completed']:
        last_completed = datetime.strptime(habit['last_completed'], "%Y-%m-%d").date()
        if last_completed == today - timedelta(days=1):
            habit['streak'] += 1
        else:
            habit['streak'] = 1
    else:
        habit['streak'] = 1

    habit['last_completed'] = str(today)
    save_habits(habits)
    refresh_listbox()

def delete_habit():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("No selection", "Select a habit to delete.")
        return
    idx = selected[0]
    habits = load_habits()
    habit_name = habits[idx]['name']
    if messagebox.askyesno("Delete", f"Are you sure you want to delete '{habit_name}'?"):
        habits.pop(idx)
        save_habits(habits)
        refresh_listbox()

def refresh_listbox():
    listbox.delete(0, tk.END)
    habits = load_habits()
    for habit in habits:
        listbox.insert(tk.END, f"{habit['name']} - Streak: {habit['streak']}")

# GUI Setup
root = tk.Tk()
root.title("Habit Tracker")

listbox = tk.Listbox(root, width=40, height=10)
listbox.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack()

tk.Button(btn_frame, text="Add Habit", command=add_habit).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Mark Completed", command=mark_completed).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Delete Habit", command=delete_habit).grid(row=0, column=2, padx=5)

refresh_listbox()
root.mainloop()
