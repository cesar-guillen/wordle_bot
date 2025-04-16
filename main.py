import discord
from discord.ext import tasks, commands
from bot_id import BOT_ID
from utils import *
from database import *
from graph import *
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@tasks.loop(time=new_day) 
async def update_season():
    global current_season_day
    current_season_day += 1
    if current_season_day > SEASON_DURATON:
        current_season_day = 1
        channel = bot.get_channel(CHANNEL_ID)
        overall_leaderboard_list = get_all_leaderboard(SEASON_DURATON + 1)#account that this happens at 00:00 so a new day should be added
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
        wordle_pattern = r"Wordle\s+([\d,.]+)\s+(\d+/\d+)"
        match_wordle = re.search(wordle_pattern, message.content)
        connections_pattern = r"Puzzle #(\d+)"
        match_connections = re.search(connections_pattern, message.content)
        user = message.author.display_name
        if user == None:
            user = message.author.name

        if match_wordle:
            add_user_if_not_exists(user)
            worlde_puzzle_id = int(match_wordle.group(1).replace(",", "").replace(".", ""))
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
        wordle_average = calculate_average_wordle_guesses(username_to_check, 2000)
        connections_average = calculate_average_connections_guesses(username_to_check,2000)
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

bot.run(BOT_ID)

