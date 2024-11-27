import time
import pytz
from datetime import time, datetime
SEASON_DURATON = 28
SEASON_START_DATE = "28/10/2024"
WORDLE_0 = "19/6/2021"
CONNECTIONS_0 = "11/6/2023"

def day_difference(first_date, second_date):
    day_difference = (first_date - second_date).days
    return day_difference

def calculate_season_day(today, season_start_date): 
    return (day_difference(today,season_start_date) % SEASON_DURATON) + 1

new_day = time(hour=23, minute=0)  #this uses utc times
season_start_date = datetime.strptime(SEASON_START_DATE, "%d/%m/%Y")
cet = pytz.timezone("Europe/Berlin")

def find_cet_day():    
    global cet
    today = datetime.now(pytz.utc)
    return today.astimezone(cet)

today_cet = find_cet_day() # server is in utc timezone, changing it to CET
season_start_date_cet = cet.localize(season_start_date)
current_season_day = calculate_season_day(today_cet, season_start_date_cet)

