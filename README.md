# Discord Bot for Wordle and Connections Leaderboards

This project is a Discord bot designed to track and display Wordle and Connections scores for users, generate leaderboards, and manage season statistics.

## Features

- **Score Tracking**:
  - Automatically tracks Wordle and Connections scores submitted in a Discord channel.
  - Stores user data in a SQLite database.

- **Leaderboards**:
  - Generates leaderboards for Wordle, Connections, and combined scores.
  - Displays daily, seasonal, and all-time rankings.

- **Statistics**:
  - Calculates individual user statistics, including average guesses and distribution of scores.

- **Season Management**:
  - Manages seasons with configurable durations (default is 28 days).
  - Automatically generates and posts end-of-season results.

## Commands

### `/rank <w|c|a> [days]`
Displays leaderboards for:
- **w** - Wordle
- **c** - Connections
- **a** - All games combined  

Optionally, specify the number of days (default is all-time).


### `/season`
Displays the current season leaderboard. Seasons last 28 days by default. At the end of a season, results are posted, and a new season begins automatically.

Example output:

Current Season results day 25/28:
1. user1: 5.28
2. user2: 4.62
3. user3: 4.12
4. user4: 4.12

### `/stats @user`
Displays a user’s statistics, including their average guesses and distribution for Wordle and Connections.

Example output:

#### Average in Wordle: 4.05  
1/6 -> 0.00%  
2/6 -> 0.00%  
3/6 -------------------> 36.36%  
4/6 ------------------> 34.09%  
5/6 -----------> 20.45%  
6/6 ----> 6.82%  
X/6 --> 2.27%  

#### Average correct Connections: 1.57  
0 ----------> 22.73%  
1 --------------> 34.09%  
2 ----------> 25.00%  
4 --------> 18.18%  
