# Stock Tracking Bot
This project was built to support a private Discord community. IYKYK, no data is provided in this repo.

No support will be provided, this is provided as-is. I'm not a programmer, if you see a problem fix it and pull request.

Use Issues for new suggestions and issues.

Before installing, be aware this bot uses the Tradier API. You will need an account to run this bot. https://documentation.tradier.com/

All data is stored in `stocks.json`. This is private data and not included in the repo. A template JSON file will be created on first start.

## 🧑🏻‍💻 Usage
- `/today` Lists any plays for today.
- `/upcoming` List any upcoming plays
- `/rsa` Search past stocks
- `/new` Adds a new stock to the list
- `/edit` Edit a stock in the database
- `/brokers` Allows people to report when shares are available for past RSAs
- `/confirm` Allows you to confirm if an RSA rounded or went CIL. This also removes it from the RSA Bulletin and moves it to the 'past' list.
- `/delete` Used to delete a stock from the DB. This is mainly used for mistakes, as we want to track past RSAs.

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

### 3. Add secrets.py
```bash
nano secrets.py
```
Paste the following and fill:
```bash
DISCORD_TOKEN = ''
TRADIER_API_KEY = ''
DISCORD_GUILD = []
DISCORD_CHANN = []
```

### 4. Run
```bash
python3 rsa.py
```
