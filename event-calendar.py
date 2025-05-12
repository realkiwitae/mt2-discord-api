import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone,timedelta
import pytz
import json

EVENTS_ICON_PATH = "/home/lys/Desktop/folder/bisousnours/icons/"

# Load configuration
CONFIG_FILE = "config.json"
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found. Please create it.")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

WEBHOOK_URL = config["WEBHOOK_URL"]
DISCORD_API_BASE = config["DISCORD_API_BASE"]
GUILD_ID = config["GUILD_ID"]
BOT_TOKEN = config["BOT_TOKEN"]
URL = config["URL_EVENT"]
LOCAL_FILE = config["LOCAL_FILE"]
YEAR = config["YEAR"]
force = False
YEAR = 2025
force = False

def get_calendar_text():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")
    target_header = soup.find("span", {"id": "Europe_.7C_Germania_.7C_Teutonia"})
    table = target_header.find_next("table")
    
    rows = table.find_all("tr")[1:]
    lines = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            day = cols[0].get_text(" ", strip=True)

            # we can have multiple events in one day 1 per column
            for i in range(1, len(cols)):
                event = cols[i].get_text(",", strip=True).replace("\n", ",")
                if len(event) > 10 and not any(txt in event for txt in ["Aide quête dada","Attraper"]):
                    lines.append(f"{day},{event}")
    # Remove duplicates and sort by date    
    return "\n".join(lines)

def load_last_calendar():
    if not os.path.exists(LOCAL_FILE):
        return ""
    with open(LOCAL_FILE, "r", encoding="utf-8") as f:
        return f.read()

def save_calendar(content):
    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def send_to_discord(content):
    payload = {
        "username": "Calendrier Metin2",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/fr/d/d7/Metin2_Logo.png",
        "content": "**📅 Calendrier des événements Metin2 (Europe)**\n" + "\n".join(f"**{line}" for line in content.splitlines())
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    return response.status_code == 204


def format_scheduled_time(day, time_range):

    # Example inputs: day = "6 Mai", time_range = "17h à 19h"
    day_parts = day.split(" ")
    day_number = day_parts[0].replace("er", "")  # Remove "er" from "1er"
    month_name = day_parts[1]

    # Map French month names to numbers
    month_mapping = {
        "Jan": "01", "Fév": "02", "Mar": "03", "Avr": "04", "Mai": "05",
        "Juin": "06", "Juil": "07", "Août": "08", "Sep": "09", "Oct": "10",
        "Nov": "11", "Déc": "12"
    }
    month_number = month_mapping[month_name]

    if "Toute la journée" in time_range:
        # Handle all-day events
        start_time = "00:00:00"
        end_time = "23:59:59"
        return f"{YEAR}-{month_number.zfill(2)}-{day_number.zfill(2)}T{start_time}Z", f"{YEAR}-{month_number.zfill(2)}-{day_number.zfill(2)}T{end_time}Z"
    # Extract start time (e.g., "17h" -> "17:00")
    start_hour = time_range.split("h")[0].strip()
    if "à" in time_range:
        end_hour = time_range.split("à")[1].split("h")[0].strip()
    else:
        end_hour = str(int(start_hour) + 1).strip()  # Default to 2 hours later if not specified
    
    start_time = f"{start_hour}:00:00"
    end_hour = f"{end_hour}:00:00"

    # Combine into ISO 8601 format
    date = f"{YEAR}-{month_number.zfill(2)}-{day_number.zfill(2)}"
    scheduled_start_time = f"{date}T{start_time}Z"
    scheduled_end_time = f"{date}T{end_hour}Z"
    
    if end_hour < start_hour:
        # use time library to increase the date by 1 day
        print(f"Debug: scheduled_end_time = {scheduled_end_time}")
        end_dt = datetime.strptime(scheduled_end_time, "%Y-%m-%dT%H:%M:%SZ")
        end_dt += timedelta(days=1)
        scheduled_end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return scheduled_start_time ,scheduled_end_time

def create_discord_event(day, time_range, event):
    url = f"{DISCORD_API_BASE}/guilds/{GUILD_ID}/scheduled-events"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Format the date to match Discord's expected format
    SD,ED = format_scheduled_time(day, time_range)

    print(f"Debug: Raw SD = {SD}, Raw ED = {ED}")
    # Check if event is in the past
    paris_tz = pytz.timezone("Europe/Paris")  # Define Paris timezone

    # Convert SD and ED from Paris time to UTC
    paris_tz = pytz.timezone("Europe/Paris")
    start_dt_paris = paris_tz.localize(datetime.strptime(SD, "%Y-%m-%dT%H:%M:%SZ"))
    end_dt_paris = paris_tz.localize(datetime.strptime(ED, "%Y-%m-%dT%H:%M:%SZ"))

    # Convert to UTC
    start_dt_utc = start_dt_paris.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_dt_utc = end_dt_paris.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if(start_dt_utc < current_time_utc):
        print(f"⏳ Skipping past event: {event} on {day}")
        return False



    # add image to event

    event_mapping = {
        "Certificat": "https://fr-wiki.metin2.gameforge.com/index.php/Supermontures",
        "Bénédiction": "https://fr-wiki.metin2.gameforge.com/index.php/B%C3%A9n%C3%A9diction_mineure",
        "Draconis" : "https://fr-wiki.metin2.gameforge.com/index.php/Cor_Draconis_(brut)",
        "Lecture" : "https://fr-wiki.metin2.gameforge.com/index.php/Lecture_concentr%C3%A9e",
        "Haricot-dragon": "https://fr-wiki.metin2.gameforge.com/index.php/Haricot-dragon_vert",
        "Tissu": "https://fr-wiki.metin2.gameforge.com/index.php/Tissu_fin",
        "pourpre": "https://fr-wiki.metin2.gameforge.com/index.php/Bo%C3%AEte_d%27%C3%A9b%C3%A8ne_pourpre",
        "Enchanté": "https://fr-wiki.metin2.gameforge.com/index.php/Objet_enchant%C3%A9_(b)",
        "Anneau": "https://fr-wiki.metin2.gameforge.com/index.php/Anneau_de_t%C3%A9l%C3%A9portation",
        "puzzle": "https://fr-wiki.metin2.gameforge.com/index.php/Le_puzzle_du_poisson",
        "exorcisme": "https://fr-wiki.metin2.gameforge.com/index.php/Parchemin_d%27exorcisme",
        "renforcement": "https://fr-wiki.metin2.gameforge.com/index.php/Objet_de_renforcement",
        "Flamme": "https://fr-wiki.metin2.gameforge.com/index.php/Flamme_du_dragon_(B)",
        "rayon de Lune": "https://fr-wiki.metin2.gameforge.com/index.php/Coffre_de_rayon_de_Lune"
    }


    # Description: 
    emoji = ""
    for key, value in event_mapping.items():
        if key in event:
            emoji = value
            break
    if(emoji == ""):
        description = f"{event} on {day}"
    else:
        description = f"[{event}]({emoji}) on {day}" if emoji.startswith("http") else f"{event} on {day}"

    # Convert month name to number

    payload = {
        "name": event,
        "scheduled_start_time": start_dt_utc,  
        "scheduled_end_time": end_dt_utc, 
        "privacy_level": 2,  # GUILD_ONLY
        "entity_type": 3,  # EXTERNAL
        "entity_metadata": {
            "location": "Metin2 Event Location"
        },
        "description": description,
    }

    print(f"Debug: Creating event with payload: {payload}")

    response = requests.post(url, headers=headers, json=payload)

    print(f"Debug: {response.status_code}")
    if response.status_code == 201 or response.status_code == 204 or response.status_code == 200:
        print(f"✅ Event '{event}' created successfully.")
        return True
    else:
        print(f"❌ Failed to create event '{event}'. Response: {response.text}")
        return True


# Programme principal
current_calendar = get_calendar_text()
last_calendar = load_last_calendar()

if current_calendar != last_calendar or force==True:

    for line in current_calendar.splitlines():

        day,time_range,event = line.split(",",2)
        if create_discord_event(day, time_range, event):
            # Wait 15 seconds between event creations
            import time
            time.sleep(15)
        
        

else:
    print("⏸️ Aucune modification détectée. Rien envoyé.")


# # Send todays events
# if send_to_discord(current_calendar):
#     print("✅ Nouveau calendrier envoyé.")
#     save_calendar(current_calendar)

# else:
#     print("❌ Erreur lors de l'envoi.")