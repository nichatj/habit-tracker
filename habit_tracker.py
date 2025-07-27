import json
import os
from datetime import datetime, date, timedelta


DATA_FILE = 'habit_data.json'
#Global variable
last_deleted_habit = None

##Core##
#Load habits from file 
def load_habits():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, 'r') as f:
            habits = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

    # Ensure all required fields are present
    for habit in habits:
        habit.setdefault('streak', 0)
        habit.setdefault('last_completed', None)

    return habits

    
#Save habits to file 
def save_habits(habits):
    with open(DATA_FILE, 'w') as f:
        json.dump(habits, f, indent=4)

# Add new habit
def add_habit(name):
    habits =load_habits()
    habits.append(
        {
            'name' : name,
            'created' : str(date.today()), 
            'last_completed' : None, 
            'streak' :0, 
            'history' : []
        }
    )
    save_habits(habits)
    print(f"Habit '{name}' added.")

#Delete habit
def delete_habit(index):
    global last_deleted_habit
    habits = load_habits()
    last_deleted_habit = habits.pop(index)
    save_habits(habits)
    print(f"Habit '{last_deleted_habit['name']}' has been deleted. You can undo it.")

#Undo delete habit
def undo_delete():
    global last_deleted_habit
    if last_deleted_habit is None:
        print("No resent habit to resotre. ")
        return
    
    habits = load_habits()
    habits.append(last_deleted_habit)
    save_habits(habits)
    print(f"Habit '{last_deleted_habit['name']}' has been restored.")
    last_deleted_habit = None

#View all habits 
def view_habits():
    habits = load_habits()
    if not habits:
        print("No habits to show.")
        return

    print("\nYour Habits:")
    print("-" * 30)
    for idx, habit in enumerate(habits, start=1):
        print(f"{idx}. {habit['name']} - Streak: {habit['streak']}")
##end core functions##

## add extras  ##
#Mark the completed task 
def mark_completed(index):
    habits = load_habits()
    today = date.today()
    habit = habits[index]

    if habit["last_completed"] == str(today):
        print(f" '{habit['name']} is already marked as DONE today. Well done :D")
        return
    
    # Append today's date to history (if not already added)
    if "history" not in habit:
        habit["history"] = []

    if str(today) not in habit["history"]:
        habit["history"].append(str(today))


    
    #convert last_completed to date obj 
    last_date = habit["last_completed"]
    if last_date:
        last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
    else:
        last_date= None
    
    #update streak
    if last_date == today - timedelta(days=1):
        habit["streak"] += 1
    else:
        habit["streak"] = 1
    
    habit["last_completed"] = str(today)
    save_habits(habits)
    print(f"Marked '{habit['name']} as completed for today.")


def calculate_stats(habit):
    # Remove duplicates before converting to date objects
    unique_history = list(set(habit.get("history", [])))
    if not unique_history:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_completed": 0,
            "completion_rate": "0%"
        }

    # Convert to date objects
    dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in unique_history]
    dates.sort()

    total_completed = len(dates)
    today = date.today()
    current_streak = 0
    longest_streak = 0
    streak = 0

    for i in range(len(dates)):
        if i == 0:
            streak = 1
        else:
            if (dates[i] - dates[i - 1]).days == 1:
                streak += 1
            else:
                longest_streak = max(longest_streak, streak)
                streak = 1

    longest_streak = max(longest_streak, streak)

    # Determine current streak
    if dates[-1] == today:
        if len(dates) > 1 and (today - dates[-2]).days == 1:
            current_streak = streak
        else:
            current_streak = 1
    elif dates[-1] == today - timedelta(days=1):
        current_streak = 1
    else:
        current_streak = 0

    created_date = datetime.strptime(habit["created"], "%Y-%m-%d").date()
    days_active = (today - created_date).days + 1
    completion_rate = f"{round((total_completed / days_active) * 100)}%"

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_completed": total_completed,
        "completion_rate": completion_rate
    }



#Main 
def main():
    while True:
        print("\n" + "="*40)
        print("📅  Habit Tracker".center(40))
        print("="*40)
        print("1. View habits 📋")
        print("2. Add habit 📍")
        print("3. Mark habit as Completed ✅")
        print("4. View habit history 📅")
        print("5. View habit stats 📊")
        print("6. Delete a habit 🗑️")
        print("7. Undo last deletion ↩️")
        print("8. Exit")
        print("="*40)

        print("\nPlease select your option (1–8):")
        choice = input("> ")

        if choice == '1':
            view_habits()
        elif choice == '2':
            name = input("Enter new habit name: ")
            add_habit(name)
        elif choice == '3':
            habits = load_habits()
            if not habits:
                print("No habits to complete.")
                continue
            print("\nWhich habit did you complete today?")
            for idx, habit in enumerate(habits, start=1):
                print(f"{idx}. {habit['name']} (streak: {habit['streak']})")
            try:
                selected = int(input("Enter number: ")) -1 
                if 0 <= selected < len(habits):
                    mark_completed(selected)
                else:
                     print("Invalid number.")
            except ValueError:
                print("Please enter the valid number.")

        elif choice == '4':
            habits = load_habits()
            if not habits:
                print("No habits yet.")
                continue
            for idx, habit in enumerate(habits, start=1):
                print(f"\n{idx}. {habit['name']} - History:")
                for date_str in sorted(habit.get("history", [])):
                    print(f"   • {date_str}")
    
        elif choice == '5':
            habits = load_habits()
            if not habits:
                print("No habits yet.")
                continue
            for idx, habit in enumerate(habits, start=1):
                stats = calculate_stats(habit)
                print(f"\n{idx}. {habit['name']}")
                print(f"   • Total days completed: {stats['total_completed']}")
                print(f"   • Current streak: {stats['current_streak']}")
                print(f"   • Longest streak: {stats['longest_streak']}")
                print(f"   • Completion rate: {stats['completion_rate']}")
        elif choice == '6':
            habits = load_habits()
            if not habits:
                print("No habits to delete.")
                continue
            print("\n Which habit do you want to delete?")
            for idx, habit in enumerate(habits, start=1):
                print(f"{idx}. {habit['name']}")
            try:
                selected = int(input("Enter number to delete: ")) - 1
                if 0 <= selected < len(habits):
                    delete_habit(selected)
                else:
                    print("Invalid number.")
            except ValueError:
                print("Please enter a valid number.")
        elif choice == '7':
            undo_delete()
        elif choice == '8':
            print("Good BYE. See you later.")
            break
        else:
            print("Invalid selection.")

os.system('clear')
if __name__== '__main__':
    main()

