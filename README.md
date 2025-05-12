# mt2-discord-api
Giving you the tools to improve your Metin2 experience on discord


## Setup

0. Use a venv its cleaner
```shell
python3 -m venv .venv        
source .venv/bin/activate
```

1. **Install Dependencies**:
   Make sure you have Python installed. Install the required libraries using:
   ```bash
   pip install -r requirements.txt
   ```

2. Create the Configuration File: Create a file named config.json in the same directory as the script. Use the format of config_template.json

```json
{
    "WEBHOOK_URL": "https://ptb.discord.com/api/webhooks/your_webhook_id/your_webhook_token",
    "DISCORD_API_BASE": "https://discord.com/api/v10",
    "GUILD_ID": "your_guild_id",
    "BOT_TOKEN": "your_bot_token",
    "URL_EVENT": "https://fr-wiki.metin2.gameforge.com/index.php/Calendrier_%C3%A9v%C3%A9nement",
    "LOCAL_FILE": "last_calendar.txt",
    "YEAR": 2025
}
```

Replace the placeholders (your_webhook_id, your_webhook_token, your_guild_id, your_bot_token) with your actual values.

### Event Calendar Script

This script fetches event data from the Metin2 Wiki and creates scheduled events in a Discord server.
Run it using: 
```shell
 python event-calendar.py
```

## Notes

a. Ensure that the bot has the necessary permissions in your Discord server to manage events.

b. *Keep the config.json file private* and do not share it publicly to avoid exposing sensitive information.