import sqlite3
import math
from datetime import datetime
from day_functions import *

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

def get_all_users():
    query = database.execute('SELECT Username FROM Users').fetchall()
    return query

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
    today_cet = find_cet_day()
    season = int(math.ceil(day_difference(today_cet, season_start_date_cet) / 7) / 4)
    users = []
    rank = []
    for idx, (user, score) in enumerate(rank_list, 1):
        users.append(user)
        rank.append(idx)
    for i in range(len(users)):
        database.execute('INSERT INTO SeasonResults (UserID, Season, Position) VALUES (?,?,?)',
                         (users[i],season,rank[i]))
        database.commit()