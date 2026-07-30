# Stock Tracking Bot
This project was built to support a private Discord community. IYKYK, no data is provided in this repo.

Before installing, be aware this bot uses the Tradier API. You will need an account to run this bot. https://documentation.tradier.com/

All data is stored in `stocks.json`. This is private data and not included in the repo. A template JSON file will be created on first start.

## 🧑🏻‍💻 Usage
- `/today` Lists any plays for today.
- `/upcoming` List any upcoming plays (today and future dates only)
- `/old` Lists plays past their split date that still need a `/confirm`
- `/rsa` Search past stocks
- `/new` Adds a new stock to the list
- `/edit` Edit a stock in the database
- `/brokers` Allows people to report when shares are available for past RSAs
- `/confirm` Allows you to confirm if an RSA rounded or went CIL. This also removes it from the RSA Bulletin and moves it to the 'past' list.
- `/export` Export every RSA to date as a CSV, with optional start/end date filtering. Only visible to the requester.
- `/delete` Used to delete a stock from the DB. This is for mistakes only and asks for confirmation before deleting — use `/confirm` to clear finished plays.

Anything left unconfirmed for more than a week past its split date is automatically archived to the past list, so the bulletin cleans itself — no data is ever deleted. Commands only work in servers, not DMs. The bot reconnects on its own if Discord is unreachable.

## 🛠️ Installation    

### 1. Create your Discord App
- Read the docs, https://discord.com/developers/docs/getting-started
- Once created go to Bot -> Privileged Gateway Intents -> Enable `Presence Intent`, `Server Members Intent`, `Message Content Intent`
- Reset your token and save it
- Navigate to OAuth2 -> URL Generator -> under SCOPES check `bot`. Under BOT PERMISSIONS check `Read Messages/View Channels` and `Send Messages`
- Copy the URL and paste it in your browser to invite to your Discord server.

### 2. Prepare your environment
```bash
git clone https://github.com/zeusec/bot-iykyk
cd bot-iykyk
python -m venv venv
pip install discord-py-interactions --upgrade
pip install requests
```

### 3. Add config.py
```bash
nano config.py
```
Paste the following and fill:
```bash
DISCORD_TOKEN = ''
TRADIER_API_KEY = ''
DISCORD_CHANN = []
```

### 4. Run
```bash
python3 rsa.py
```
