from database import *
from utils import *
import csv 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import timedelta

def prepare_data_for_x_days(number_days):
    query = database.execute("SELECT WordleID FROM WordleScores ORDER BY ScoreID DESC LIMIT 1")
    last_wordle_id = int(query.fetchone()[0])
    date_obj = datetime.strptime(WORDLE_0, "%d/%m/%Y")
    new_date = date_obj + timedelta(days=last_wordle_id)  
    last_wordle_date = new_date.strftime("%d/%m/%Y") 
            
    first_wordle_id = last_wordle_id - number_days
    date_obj = datetime.strptime(WORDLE_0, "%d/%m/%Y")
    new_date = date_obj + timedelta(days=first_wordle_id)  
    first_wordle_date = new_date.strftime("%d/%m/%Y") 
    all_user_scores = {}
    users_list = get_all_users()
    for user in users_list:
        query = database.execute(
            "SELECT Guesses, WordleID FROM WordleScores WHERE WordleID > ? AND UserID = ?",
            (first_wordle_id, user[0])
        )
        results = query.fetchall()
        user_scores = {}
        for row in results:
            date_obj = datetime.strptime(WORDLE_0, "%d/%m/%Y")
            new_date = date_obj + timedelta(days=row[1])
            formatted_date = new_date.strftime("%d/%m/%Y")
            user_scores[formatted_date] = int(row[0].split('/')[0])

        for date, score in user_scores.items():
            if date not in all_user_scores:
                all_user_scores[date] = {}
            all_user_scores[date][user[0]] = score
        write_csv(first_wordle_date,last_wordle_date, users_list, all_user_scores)

def write_csv(first_wordle_date, last_wordle_date, users_list, all_user_scores):
    with open("combined_scores.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        first_date = datetime.strptime(first_wordle_date, "%d/%m/%Y")
        last_date = datetime.strptime(last_wordle_date, "%d/%m/%Y")
        date_range = [
            (first_date + timedelta(days=i)).strftime("%d/%m/%Y")
            for i in range((last_date - first_date).days + 1)
        ]
        header = ["Date"] + [f"{user[0]}" for user in users_list]
        writer.writerow(header)

        for date in date_range:
            row = [date]  
            for user in users_list:
                user_id = user[0]
                score = all_user_scores.get(date, {}).get(user_id, -1)
                row.append(score)
            writer.writerow(row)

def plot_graph():
    data = pd.read_csv('combined_scores.csv')
    data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')
    data.replace(-1, np.nan, inplace=True)
    data.iloc[:, 1:] = data.iloc[:, 1:].apply(pd.to_numeric)

    fig, ax = plt.subplots()
    ax.set_xlim(data['Date'].min(), data['Date'].max())
    ax.set_ylim(1, 6)
    
    ax.set_title('Average Wordle')
    ax.set_xlabel('Date')
    ax.set_ylabel('Average Score')
    ax.grid(True)

    lines = {}
    for user in data.columns[1:]:
        line, = ax.plot([], [], label=user)
        lines[user] = line

    def update(frame):
        current_data = data.iloc[:frame + 1]
        for user in data.columns[1:]:
            current_avg = current_data[user].expanding().mean()
            lines[user].set_data(current_data['Date'], current_avg)
        ax.legend(loc='upper left')
        return lines.values()

    ani = animation.FuncAnimation(
        fig, update, frames=len(data), blit=False, interval=500, repeat=False
    )
    plt.xticks(rotation=45)
    plt.tight_layout()
    ani.save("cumulative_average_animation.gif", writer="pillow")
    
