import discord
from discord.ext import tasks
import re
import sqlite3
import math 
import time
from datetime import time, datetime, timedelta
import csv 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import asyncio 
from bot_id import BOT_ID
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

#CHANNEL_ID = 944387424426029056
CHANNEL_ID = 1303707032842403854

WORDLE_0 = "19/6/2021"
CONNECTIONS_0 = "11/6/2023"

def day_difference(first_date, second_date):
    day_difference = (first_date - second_date).days
    return day_difference

def calculate_season_day(today, season_start_date): 
    return (day_difference(today,season_start_date) % SEASON_DURATON) + 1
    
SEASON_DURATON = 28
SEASON_START_DATE = "28/10/2024"
season_start_date = datetime.strptime(SEASON_START_DATE, "%d/%m/%Y")
today = datetime.today()
current_season_day = calculate_season_day(today, season_start_date)
new_day = time(hour=23, minute=0) # this uses UTC time 

#database
database = sqlite3.connect('bot_db')
cursor = database.cursor
database.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT NOT NULL UNIQUE
    )
''')

database.execute('''
    CREATE TABLE IF NOT EXISTS WordleScores (
        ScoreID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER,
        WordleID INTEGER,
        Guesses INTEGER NOT NULL,
        FOREIGN KEY(UserID) REFERENCES Users(UserID)
    )
''')

database.execute('''
    CREATE TABLE IF NOT EXISTS ConnectionsScores (
        ScoreID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER,
        ConnectionsID INTEGER,
        Score INTEGER NOT NULL,
        FOREIGN KEY(UserID) REFERENCES Users(UserID)
    )
''')

database.execute('''
    CREATE TABLE IF NOT EXISTS SeasonResults (
        SeasonScoreID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER,
        Season INTEGER,
        Position INTEGER,
        FOREIGN KEY(UserID) REFERENCES Users(UserID)
    )
    ''')

database.commit()

@tasks.loop(time=new_day) 
async def update_season():
    global current_season_day
    current_season_day += 1
    if current_season_day > SEASON_DURATON:
        current_season_day = 1
        channel = bot.get_channel(CHANNEL_ID)
        overall_leaderboard_list = get_all_leaderboard(SEASON_DURATON)
        leaderboard_message = "End season results:\n"
        for idx, (user, score) in enumerate(overall_leaderboard_list, 1):
            leaderboard_message += f"{idx}. {user}: {round(score, 2)}\n"
        await channel.send(leaderboard_message)
        put_season_results(overall_leaderboard_list)

@bot.event
async def on_ready():
    if not update_season.is_running():
        update_season.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if "sigh" in message.content.lower(): 
        await message.channel.send(":index_pointing_at_the_viewer: :joy: jordi")
        
    if message.channel.id == CHANNEL_ID:
        message.content = message.content.replace("X", "7")
        wordle_pattern = r"Wordle\s+([\d,]+)\s+(\d+/\d+)"
        match_wordle = re.search(wordle_pattern, message.content)
        connections_pattern = r"Puzzle #(\d+)"
        match_connections = re.search(connections_pattern, message.content)
        user = message.author.display_name
        if user == None:
            user = message.author.name

        if match_wordle:
            add_user_if_not_exists(user)
            worlde_puzzle_id = int(match_wordle.group(1).replace(",", ""))
            score = match_wordle.group(2)
            put_wordle(user, worlde_puzzle_id, score)
            await message.channel.send(f"Wordle Puzzle #{worlde_puzzle_id}, Score: {score}")

        elif match_connections:
            add_user_if_not_exists(user)
            conn_puzzle_id = int(match_connections.group(1))
            lines = message.content.splitlines()[2:]
            correct_groups = 0

            for line in lines:
                emojis = line.strip()
                
                if len(set(emojis)) == 1:  
                    correct_groups += 1
            put_connections(user, conn_puzzle_id, correct_groups)
            await message.channel.send(f"Puzzle ID: {conn_puzzle_id}, Correct Groups: {correct_groups}")

        await bot.process_commands(message)

@bot.command()
async def stats(ctx):
    mentioned_user = ctx.message.mentions
    user = mentioned_user[0]  
    username_to_check = user.nick if user.nick else user.global_name if user.global_name else user.name
    cursor = database.execute('SELECT Username FROM Users WHERE Username = ?', (username_to_check,))
    result = cursor.fetchone()  
    if result: 
        wordle_average = calculate_average_wordle_guesses(username_to_check)
        connections_average = calculate_average_connections_guesses(username_to_check)
        wordle_distribution = calculate_wordle_distribution(username_to_check)
        connections_distribution = calculate_connections_distribution(username_to_check)
        await ctx.send(f"## Average in Worlde: {wordle_average:.2f}\n{wordle_distribution}\n## Average correct Connections: {connections_average:.2f}\n{connections_distribution}") 

    else:
        await ctx.send("User not found. Send a Wordle or Connections first.")
        

@bot.command()
async def movie(ctx):
    message_content = ctx.message.content
    parts = message_content.split()
    help = "Please specify the number of days after the command."
    if len(parts) == 2 :
        if parts[1][0] == 'h':
            await ctx.send(f"{help}")
        else:
            try:
                number_days = int(parts[1]) - 1    
            except:
                await ctx.send(f"Please enter a number, use /movie help to display the help menu.")
                return
            if number_days < 1:
                await ctx.send(f"{help}")
                return
            if number_days > 100:
                await ctx.send(f"You are not crashing my bot gtfo")
            prepare_data_for_x_days(number_days)
            plot_graph()
            await ctx.send("", file=discord.File('cumulative_average_animation.gif'))              
    else:
        await ctx.send(f"{help}")

@bot.command()
async def rank(ctx):
    game = ((ctx.message.content.split())[1])[0].lower()
    try:
        days = int((ctx.message.content.split())[2])
    except:
        days = 2000
    if game == "w":
        wordle_leaderboard_list = get_wordle_leaderboard(days)
        leaderboard_message = "Wordle Leaderboard:\n"
        for idx, (user, score) in enumerate(wordle_leaderboard_list, 1):
            leaderboard_message += f"{idx}. {user}: {round(score, 2)}\n"
        await ctx.send(leaderboard_message)
        return
    if game == "c": 
        connections_leaderboard_list = get_connections_leaderboard(days)
        leaderboard_message = "Connections Leaderboard:\n"
        for idx, (user, score) in enumerate(connections_leaderboard_list, 1):
            leaderboard_message += f"{idx}. {user}: {round(score, 2)}\n"
        await ctx.send(leaderboard_message)
        return
    if game == "a": 
        overall_leaderboard_list = get_all_leaderboard(days)
        leaderboard_message = "Overall Leaderboard:\n"
        for idx, (user, score) in enumerate(overall_leaderboard_list, 1):
            leaderboard_message += f"{idx}. {user}: {round(score, 2)}\n"
        await ctx.send(leaderboard_message)
        return
    else:
        await ctx.send(f"{game} is not a command. Please specify a leaderboard: Wordle (w), Connections (c), or All (a).")

@bot.command()
async def season(ctx):
    global current_season_day
    overall_leaderboard_list = get_all_leaderboard(current_season_day)
    leaderboard_message = f"Current Season results day {current_season_day}/28:\n"
    for idx, (user, score) in enumerate(overall_leaderboard_list, 1):
        leaderboard_message += f"{idx}. {user}: {round(score, 2)}\n"
    await ctx.send(leaderboard_message)
    return
         
def get_all_users():
    query = database.execute('SELECT Username FROM Users').fetchall()
    return query

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
    

def calculate_connections_distribution(username_to_check):
    distribution = []
    query = database.execute('SELECT COUNT(*) FROM ConnectionsScores WHERE UserID = ?', (username_to_check,))
    total_count = query.fetchone()[0]
    for i in range(5):
        if i == 3:
            continue
        query = database.execute('SELECT COUNT(*) FROM ConnectionsScores WHERE Score = ? AND UserID = ?', (i, username_to_check))
        count = query.fetchone()[0]
        percentage = (count / total_count) * 100
        num_dashes = math.ceil((count / total_count) * 40)
        if num_dashes == 0:
            num_dashes = 1
        distribution_line = f'{i} ' + '-' * num_dashes + f'> {percentage:.2f}%'
        distribution.append(distribution_line)

    formatted_distribution = '\n'.join(distribution)
    return formatted_distribution

def calculate_wordle_distribution(username_to_check):
    distribution = []
    query = database.execute('SELECT COUNT(*) FROM WordleScores WHERE UserID = ?', (username_to_check,))
    total_count = query.fetchone()[0]

    for i in range(7):
        score_to_check = f'{i + 1}/6'
        query = database.execute('SELECT COUNT(*) FROM WordleScores WHERE Guesses = ? AND UserID = ?', (score_to_check, username_to_check))
        count = query.fetchone()[0]
        percentage = (count / total_count) * 100
        num_dashes = math.ceil((count / total_count) * 50)
        if num_dashes == 0:
            num_dashes = 1
        if i == 6:
            score_to_check = 'X/6'
        distribution_line = f'{score_to_check} ' + '-' * num_dashes + f'> {percentage:.2f}%'
        distribution.append(distribution_line)

    formatted_distribution = '\n'.join(distribution)
    
    return formatted_distribution

    
def get_wordle_leaderboard(days):
    users_list = get_all_users()
    wordle_leaderboard_list = []
    for users in users_list:
        user = users[0]
        user_wordle_average = calculate_average_wordle_guesses(user,days)
        wordle_leaderboard_list.append((user,user_wordle_average))
    wordle_leaderboard_list.sort(key=lambda x: x[1])
    return wordle_leaderboard_list

def get_connections_leaderboard(days):
    users_list = get_all_users()
    connections_leaderboard_list = []
    for users in users_list:
        user = users[0]
        user_connections_average = calculate_average_connections_guesses(user,days)
        connections_leaderboard_list.append((user,user_connections_average))
    connections_leaderboard_list.sort(key=lambda x: x[1], reverse=True)
    return connections_leaderboard_list

def get_all_leaderboard(days):
    connections_leaderboard_list = get_connections_leaderboard(days)
    wordle_leaderboard_list = get_wordle_leaderboard(days)
    overall_leaderboard_list = []
    for c_user in connections_leaderboard_list:
        for w_user in wordle_leaderboard_list:
            if c_user[0] == w_user[0]:
                overall_leaderboard_list.append((c_user[0],(7.0-w_user[1])+c_user[1]))
    overall_leaderboard_list.sort(key=lambda x: x[1], reverse=True)
    return overall_leaderboard_list

def add_user_if_not_exists(username):
    database.execute('''
        INSERT OR IGNORE INTO Users (Username) VALUES (?)
    ''', (username,))
    database.commit() 

def put_connections(username, connections_id, correct):
    database.execute('INSERT INTO ConnectionsScores (UserID, ConnectionsID, Score) VALUES (?, ?, ?)', 
                   (username, connections_id, correct))
    database.commit()

def put_wordle(username, wordle_id, correct):
    database.execute('INSERT INTO WordleScores (UserID, WordleID, Guesses) VALUES (?, ?, ?)', 
                   (username, wordle_id, correct))
    database.commit()
    
def put_season_results(rank_list):
    global season_start_date
    today = datetime.today()
    season = int(math.ceil(day_difference(today, season_start_date) / 7) / 4)
    users = []
    rank = []
    for idx, (user, score) in enumerate(rank_list, 1):
        users.append(user)
        rank.append(idx)
    for i in range(len(users)):
        database.execute('INSERT INTO SeasonResults (UserID, Season, Position) VALUES (?,?,?)',
                         (users[i],season,rank[i]))
        database.commit()

def calculate_start_id(days):
    WORDLE_0 = "19/6/2021"
    start_date_w = datetime.strptime(WORDLE_0, "%d/%m/%Y")
    start_date_c = datetime.strptime(CONNECTIONS_0, "%d/%m/%Y")
    today_date = datetime.today()
    start_id_w = day_difference(today_date, start_date_w) - days
    start_id_c = day_difference(today_date, start_date_c) - days
    return [start_id_w, start_id_c]

def calculate_average_wordle_guesses(username_to_check, days):
    query = database.execute('SELECT Guesses FROM WordleScores WHERE UserID = ? AND WordleID > ?', (username_to_check,calculate_start_id(days)[0]))
    guesses_db = query.fetchall() 
    guesses = []
    for row in guesses_db:
        guess_str = row[0]
        guess = int(guess_str.split('/')[0])
        guesses.append(guess)
    total_guesses = sum(guesses) 
    try:
        average_guesses = total_guesses / len(guesses)
    except:
        average_guesses = 0

    return average_guesses

def calculate_average_connections_guesses(username_to_check, days):
    query = database.execute('SELECT Score FROM ConnectionsScores WHERE UserID = ? AND ConnectionsID > ?', (username_to_check,calculate_start_id(days)[1]))
    scores_db = query.fetchall() 
    scores = []
    for row in scores_db:
        scores.append(row[0])
    total_score = sum(scores) 
    try:
        averege_score = total_score / len(scores)
    except:
        averege_score = 0
    return averege_score

bot.run(BOT_ID)

