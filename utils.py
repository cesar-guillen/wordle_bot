from database import *
from datetime import datetime
from day_functions import *
import math 

#CHANNEL_ID = 944387424426029056
CHANNEL_ID = 1303707032842403854

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
    for i, w_user in enumerate(wordle_leaderboard_list):
        if w_user[1] == 0.0:
            w_user = list(w_user) 
            w_user[1] = 7         
            wordle_leaderboard_list[i] = tuple(w_user) 
    for c_user in connections_leaderboard_list:
        for w_user in wordle_leaderboard_list:
            if c_user[0] == w_user[0]:
                overall_leaderboard_list.append((c_user[0],(7.0-w_user[1])+c_user[1]))
    overall_leaderboard_list.sort(key=lambda x: x[1], reverse=True)
    return overall_leaderboard_list

def calculate_start_id(days):
    global today_cet
    start_date_w = datetime.strptime(WORDLE_0, "%d/%m/%Y")
    start_date_c = datetime.strptime(CONNECTIONS_0, "%d/%m/%Y")
    today_date = datetime(today_cet.year, today_cet.month, today_cet.day)
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
    print(average_guesses)
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