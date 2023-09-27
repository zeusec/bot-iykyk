import logging
import requests
import json
import asyncio
import re
from interactions import Client, OptionType, slash_command, SlashContext, Embed, EmbedField, EmbedAuthor
from datetime import datetime, date
from typing import Optional
from secret import DISCORD_TOKEN, TRADIER_API_KEY, DISCORD_GUILD, DISCORD_CHANN

TAGS = ["CIL", "ROUNDED", "PENDING"]
BROKERS = ["Fidelity", "Merrill Edge", "Robinhood", "Schwab", "Tastyworks", 
           "Public", "Stocktwits", "Tradier", "Vanguard", "Ally", "Firstrade", 
           "Plynk", "BBAE", "dSPAC", "Webull", "AInvest", "Fennel", "OptionsAI", 
           "Chase", "Invstr+", "Wells Fargo", "Tornado", "SoFi"]
DAILY_BROKERS = ["Schwab", "Tastyworks", "Public", "Stocktwits", "Firstrade", "Webull", "Tradier", "BBAE", "dSPAC", "AInvest", "Chase", "Invstr+", "Tornado", "SoFi"]
EXCH_CODES = {
    'A': 'NYSE MKT',
    'B': 'NASDAQ OMX BX',
    'C': 'National Stock Exchange',
    'D': 'FINRA ADF',
    'E': 'Market Independent (Generated by Nasdaq SIP)',
    'F': 'Mutual Funds/Money Markets (NASDAQ)',
    'I': 'International Securities Exchange',
    'J': 'Direct Edge A',
    'K': 'Direct Edge X',
    'L': 'Long Term Stock Exchange',
    'M': 'Chicago Stock Exchange',
    'N': 'NYSE',
    'P': 'NYSE Arca',
    'Q': 'NASDAQ OMX',
    'S': 'NASDAQ Small Cap',
    'T': 'NASDAQ Int',
    'U': 'OTCBB',
    'V': 'OTC other',
    'W': 'CBOE',
    'X': 'NASDAQ OMX PSX',
    'G': 'GLOBEX',
    'Y': 'BATS Y-Exchange',
    'Z': 'BATS'
}

EMOJI_REDUDE = '<:9reddude:1126978459940433920>'
EMOJI_GRDUDE = '<:9greendude:1126978105085546526>'

bot = Client(token=DISCORD_TOKEN)
JSON_FILE = "stocks.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('log.txt')
    ]
)

def read_json_data(key):
    with open(JSON_FILE, 'r') as file:
        data = json.load(file)
    return data[key]

def write_json_data(key, data):
    with open(JSON_FILE, 'r') as file:
        full_data = json.load(file)
    full_data[key] = data
    with open(JSON_FILE, 'w') as file:
        json.dump(full_data, file, indent=4)

with open(JSON_FILE, 'r') as file:
    try:
        json.load(file)
    except json.JSONDecodeError:
        with open(JSON_FILE, 'w') as file:
            json.dump({"rsa": [], "research": [], "past": []}, file, indent=4)
            logging.info("Blank JSON initialized.")

# Price lookup
def get_current_price(ticker):
    url = f"https://api.tradier.com/v1/markets/quotes?symbols={ticker}"
    headers = {"Authorization": f"Bearer {TRADIER_API_KEY}", "Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        quote = data.get('quotes', {}).get('quote')
        if quote:
            return quote.get('last', 'null')
        raise KeyError("The response data did not contain the expected fields.")
    except requests.RequestException as e:
        logging.error(f"Price not found for {ticker}: {e}")
        return 'null'
    except KeyError as e:
        logging.error(f"The response data did not contain the expected fields: {e}")
        return 'null'

# Ticker lookup
def get_company_name(ticker):
    url = f"https://api.tradier.com/v1/markets/lookup?q={ticker}"
    headers = {"Authorization": f"Bearer {TRADIER_API_KEY}", "Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully received a response for {ticker}. Status Code: {response.status_code}")
        
        data = response.json()
        logging.info(f"API Response: {data}")
        
        securities = data.get('securities')
        if securities:
            security_list = securities.get('security')
            if isinstance(security_list, list):
                for security in security_list:
                    if security.get('symbol') == ticker:
                        exchange_code = security.get('exchange', 'null')
                        exchange_name = EXCH_CODES.get(exchange_code, 'Unknown')
                        return f"({security.get('description', 'null')} @ {exchange_name})"
            elif isinstance(security_list, dict):
                if security_list.get('symbol') == ticker:
                    exchange_code = security_list.get('exchange', 'null')
                    exchange_name = EXCH_CODES.get(exchange_code, 'Unknown')
                    return f"({security_list.get('description', 'null')} @ {exchange_name})"
        
        logging.error("The response data did not contain the expected fields.")
        raise KeyError("The response data did not contain the expected fields.")
        
    except requests.RequestException as e:
        logging.error(f"Company info not found for {ticker}. HTTP Request Exception: {e}")
        return 'null'
        
    except KeyError as e:
        logging.error(f"The response data did not contain the expected fields: {e}")
        return 'null'

# Update prices
async def update_stock_prices():
    while True:
        stock_data = read_json_data("rsa")
        for stock in stock_data:
            ticker = stock['Ticker']
            price = get_current_price(ticker)
            if price is not None:
                stock['Current Price'] = price
        write_json_data("rsa", stock_data)
        await asyncio.sleep(120)

# Calculate profit
def calculate_estimated_profit(price: float, split_ratio: str) -> float:
    split_ratio_num = float(split_ratio.split(":")[1]) - 1
    estimated_profit = round(price * split_ratio_num, 2)
    return estimated_profit

# Auto updates profit
async def auto_estimated_profit():
    while True:
        stock_data = read_json_data("rsa")
        for stock in stock_data:
            ticker = stock['Ticker']
            price = get_current_price(ticker)
            if price is not None:
                split_ratio = stock['Split Ratio']
                split_ratio_num = float(split_ratio.split(":")[1]) - 1
                estimated_profit = round(price * split_ratio_num, 2)
                stock['Estimated Profit'] = estimated_profit
        write_json_data("rsa", stock_data)
        await asyncio.sleep(180)

# Search RSA
@slash_command(
    name="rsa",
    description="Search a RSA",
    options=[
        {
            "name": "ticker",
            "description": "RSA ticker",
            "type": OptionType.STRING,
            "required": True
        }
    ]
)
async def rsa_stock(ctx: SlashContext, ticker: str):
    with open(JSON_FILE, 'r') as file:
        full_data = json.load(file)
    stock_data = full_data["rsa"]
    past_stock_data = full_data["past"]

    found_stock = None
    for stock in stock_data + past_stock_data:
        if stock['Ticker'].lower() == ticker.lower():
            found_stock = stock
            break

    if found_stock:
        tag = found_stock['Tag'].upper()
        tag_color = ""
        if tag == "PENDING":
            tag_color = "ffe100"
        elif tag == "ROUNDED":
            tag_color = "35e20d"
        elif tag == "CIL":
            tag_color = "cc0000"

        current_price = f"${found_stock['Current Price']}"
        estimated_profit = f"${found_stock['Estimated Profit']}"

        broker_tracking = found_stock['BrokerTracking']
        broker_list = ""
        for broker, value in broker_tracking.items():
            if value == 0:
                broker_list += f":x: {broker}\n"
            else:
                broker_list += f":white_check_mark: {broker}\n"

        embed = Embed(
            title=f"${found_stock['Ticker']} - {tag}",
            color=int(tag_color, 16),
        )
        embed.add_field(name="Current Price", value=f"`{current_price}`", inline=False)
        embed.add_field(name="Split", value=f"`{found_stock['Split Ratio']}`", inline=False)
        embed.add_field(name="Date of Split", value=f"`{found_stock['Date']}`", inline=False)
        embed.add_field(name="Estimated Profit", value=f"`{estimated_profit}`", inline=False)
        embed.add_field(name="Shares Availability", value=broker_list, inline=False)
        embed.add_field(name=found_stock['Comments'] if found_stock['Comments'] else 'Get that bread :money_mouth:', value=f"[Source]({found_stock['Source']})", inline=False)

        await ctx.send(embed=embed, ephemeral=True)
        logging.info(f"RSA '{ticker}' found and sent to Discord. Requested by {ctx.member.display_name}.")
    else:
        await ctx.send(f"RSA '{ticker}' not found.", ephemeral=True)
        logging.warning(f"RSA '{ticker}' not found. Requested by {ctx.member.display_name}.")


# Todays bulletin
@slash_command(
    name="today",
    description="Today's RSA Bulletin"
)
async def list_stocks(ctx: SlashContext):
    stock_data = read_json_data("rsa")
    if not stock_data:
        await ctx.send(f"Nothing {EMOJI_REDUDE}")
        logging.info("Today's RSA Bulletin: No stocks found. Requested by {ctx.member.display_name}.")
        return
    today = date.today()
    filtered_stocks = []
    for stock in stock_data:
        stock_date = datetime.strptime(stock['Date'], "%m-%d-%Y").date()
        if stock_date == today:
            filtered_stocks.append(stock)
            
    if not filtered_stocks:
        await ctx.send(f"Nothing {EMOJI_REDUDE}")
        logging.info("Today's RSA Bulletin: No RSAs yet. Requested by {ctx.member.display_name}.")
        return
        
    total_stocks = len(filtered_stocks)
    stocks_per_embed = 5
    total_embeds = (total_stocks + stocks_per_embed - 1) // stocks_per_embed
    for embed_number in range(total_embeds):
        start_index = embed_number * stocks_per_embed
        end_index = min(start_index + stocks_per_embed, total_stocks)
        stocks_subset = filtered_stocks[start_index:end_index]
        embed = Embed(
            title=f"Today's RSA Bulletin" + (f" - Page {embed_number + 1}/{total_embeds}" if total_embeds > 1 else ""),
            color=0x35e20d
        )
        for stock in stocks_subset:
            company_name = get_company_name(stock['Ticker'])
            ticker_name = f"**${stock['Ticker'].upper()}** {company_name}"
            ta_name = f"TA is {stock['Transfer Agent']}" if stock.get('Transfer Agent') else "TA not listed"
            post_text = f"{ticker_name}\nSplit: {stock['Split Ratio']}\nPrice: ${stock['Current Price']}\nProfit: ${stock['Estimated Profit']}\n{stock['Comments'] if stock['Comments'] else 'No comments'}\n{stock['Transfer Agent'] if stock['Transfer Agent'] else 'TA not listed'}\n[Source]({stock['Source']})"
            character_count = len(post_text)
            logging.info(f"Character count: {character_count}")
            if character_count > 2000:
                await ctx.send("Character limit exceeded. This is a bot issue.", ephemeral=True)
                logging.error("The post exceeds the character limit. Requested by {ctx.member.display_name}.")
                return
            
            embed.add_field(name="\u200b", value=ticker_name, inline=False)
            embed.add_field(name="Split", value=f"\u200b{stock['Split Ratio']}", inline=True)
            embed.add_field(name="Price", value=f"\u200b${stock['Current Price']}", inline=True)
            embed.add_field(name="Profit", value=f"\u200b${stock['Estimated Profit']}", inline=True)
            embed.add_field(name=stock['Comments'] if stock['Comments'] else 'Get that bread :money_mouth:', value=f"{ta_name}\n[Source]({stock['Source']})", inline=False)

        logging.info(f"Sending Today's RSA Bulletin - Page {embed_number + 1}/{total_embeds}")
        await ctx.send(embed=embed)

    logging.info("Today's RSA Bulletin sent successfully. Requested by {ctx.member.display_name}.")


# Upcoming RSA
@slash_command(
    name="upcoming",
    description="Upcoming RSA Bulletin"
)
async def list_upcoming_stocks(ctx: SlashContext):
    stock_data = read_json_data("rsa")
    if not stock_data:
        await ctx.send("Nothing {EMOJI_REDUDE}")
        logging.info("Upcoming RSA Bulletin: No RSAs found. Requested by {ctx.member.display_name}.")
        return

    total_stocks = len(stock_data)
    stocks_per_embed = 5
    total_embeds = (total_stocks + stocks_per_embed - 1) // stocks_per_embed
    sorted_stocks = sorted(stock_data, key=lambda x: datetime.strptime(x['Date'], "%m-%d-%Y"))

    for embed_number in range(total_embeds):
        start_index = embed_number * stocks_per_embed
        end_index = min(start_index + stocks_per_embed, total_stocks)
        stocks_subset = sorted_stocks[start_index:end_index]
        embed = Embed(
            title=f"Upcoming RSA Bulletin" + (f" - Page {embed_number + 1}/{total_embeds}" if total_embeds > 1 else ""),
            color=0x3498db
        )
        for stock in stocks_subset:
            company_name = get_company_name(stock['Ticker'])
            ticker_name = f"**${stock['Ticker'].upper()}** {company_name}"
            post_text = f"{ticker_name}\nSplit: {stock['Split Ratio']}\nPrice: ${stock['Current Price']}\nEstimated Profit: ${stock['Estimated Profit']}\nDate: {stock['Date']}\nTransfer Agent: {stock['Transfer Agent'] if stock['Transfer Agent'] else 'TA not listed'}"
            if stock['Comments']:
                post_text += f"\n{stock['Comments']}"
            post_text += f"\n[Source]({stock['Source']})"
            embed.add_field(name="\u200b", value=post_text, inline=False)

        character_count = len(embed.to_dict()["fields"][0]["value"])
        logging.info(f"Character count: {character_count}")

        if character_count > 2000:
            await ctx.send("Character limit exceeded. This is a bot issue.", ephemeral=True)
            logging.error("The post exceeds the character limit. Requested by {ctx.member.display_name}.")
            return

        logging.info(f"Sending Upcoming RSA Bulletin - Page {embed_number + 1}/{total_embeds}")
        await ctx.send(embed=embed, ephemeral=True)

    logging.info("Upcoming RSA Bulletin sent successfully. Requested by {ctx.member.display_name}.")


# New RSA
@slash_command(
    name="new",
    description="Add a RSA",
    options=[
        {
            "name": "ticker",
            "description": "RSA ticker",
            "type": OptionType.STRING,
            "required": True
        },
        {
            "name": "split_ratio",
            "description": "Split ratio",
            "type": OptionType.STRING,
            "required": True
        },
        {
            "name": "source",
            "description": "Source",
            "type": OptionType.STRING,
            "required": True
        },
        {
            "name": "date",
            "description": "Date of split (MM-DD-YYYY)",
            "type": OptionType.STRING,
            "required": False 
        },
        {
            "name": "agent",
            "description": "Transfer Agent",
            "type": OptionType.STRING,
            "required": False 
        },
        {
            "name": "comments",
            "description": "Comments",
            "type": OptionType.STRING,
            "required": False 
        }
    ]
)
async def add_stock(ctx: SlashContext, ticker: str, split_ratio: str, source: str, date: Optional[str] = None, agent: Optional[str] = None, comments: Optional[str] = ""):
    if not re.match(r'^1:\d+(\.\d+)?$', split_ratio):
        await ctx.send("Invalid split ratio. Format should be like '1:10'.", ephemeral=True)
        return

    if date is None:
        date = datetime.now().strftime("%m-%d-%Y")
    else:
        try:
            parsed_date = datetime.strptime(date, "%m-%d-%Y")
            date = parsed_date.strftime("%m-%d-%Y")
        except ValueError:
            await ctx.send("Invalid date format. Please use 'MM-DD-YYYY'.", ephemeral=True)
            return

    ticker = ticker.upper()
    stock_data = read_json_data("rsa")

    if any(stock["Ticker"].upper() == ticker for stock in stock_data):
        await ctx.send(f"RSA '{ticker}' already exists.", ephemeral=True)
        return
    
    price = get_current_price(ticker)
    if price is not None:
        price = round(price, 2)
    else:
        await ctx.send(f"Failed to fetch price for the ticker: {ticker}. Please try again.", ephemeral=True)
        return

    estimated_profit = calculate_estimated_profit(price, split_ratio)

    new_stock = {
        'Ticker': ticker,
        'Current Price': price,
        'Split Ratio': split_ratio,
        'Date': date,
        'Estimated Profit': estimated_profit,
        'Source': source,
        'Transfer Agent': agent,
        'Comments': comments,
        'Tag': 'pending',
        'BrokerTracking': {broker: 0 for broker in BROKERS}
    }

    stock_data.append(new_stock)
    write_json_data("rsa", stock_data)
    if not asyncio.get_event_loop().is_running():
        asyncio.get_event_loop().create_task(update_stock_prices())

    logging.info(f"RSA '{ticker}' added successfully. Requested by {ctx.member.display_name}.")
    date_datetime = datetime.strptime(date, "%m-%d-%Y")
    today_datetime = datetime.now()

    if date_datetime.date() == today_datetime.date():
        message = f" ${ticker} is doing a R/S today. Curently trading for ${price}. Estimated profit of ~${estimated_profit}.\n{source}"
        await ctx.send(message)
        await list_stocks(ctx)
        for channel_id in DISCORD_CHANN:
            channel = await ctx.bot.fetch_channel(channel_id)
            await channel.send(message)
    elif date_datetime.date() > today_datetime.date():
        await ctx.send(f"${ticker} has been added, last day to buy is {date}. Estimated profit of ~${estimated_profit}.")


# Modify stock
@slash_command(
    name="edit",
    description="Edit a RSA",
    options=[
        {
            "name": "ticker",
            "description": "RSA ticker",
            "type": OptionType.STRING,
            "required": True
        },
        {
            "name": "split_ratio",
            "description": "Split ratio",
            "type": OptionType.STRING,
            "required": False
        },
        {
            "name": "date",
            "description": "Date of split",
            "type": OptionType.STRING,
            "required": False
        },
        {
            "name": "agent",
            "description": "Transfer Agent",
            "type": OptionType.STRING,
            "required": False 
        },
        {
            "name": "source",
            "description": "Source",
            "type": OptionType.STRING,
            "required": False
        },
        {
            "name": "comments",
            "description": "Comments",
            "type": OptionType.STRING,
            "required": False
        },
        {
            "name": "tag",
            "description": "Shares Availability",
            "type": OptionType.STRING,
            "required": False,
            "choices": [
                {
                    "name": "ROUNDED",
                    "value": "ROUNDED"
                },
                {
                    "name": "CIL",
                    "value": "CIL"
                },
                {
                    "name": "PENDING",
                    "value": "PENDING"
                }
            ]
        }
    ]
)
async def edit_stock(ctx: SlashContext, ticker: str, split_ratio: str = None, date: str = None, source: str = None, comments: str = None, tag: str = None, agent: str = None):
    rsa_data = read_json_data("rsa")
    past_data = read_json_data("past")
    all_data = rsa_data + past_data 

    if split_ratio is not None and not re.match(r'^1:\d+(\.\d+)?$', split_ratio):
        await ctx.send("Invalid split ratio. Format should be like '1:10'.", ephemeral=True)
        return

    if date is None:
        date = datetime.now().strftime("%m-%d-%Y")
    else:
        try:
            parsed_date = datetime.strptime(date, "%m-%d-%Y")
            date = parsed_date.strftime("%m-%d-%Y")
        except ValueError:
            await ctx.send("Invalid date format. Please use 'MM-DD-YYYY'.", ephemeral=True)
            return

    for stock in all_data:
        if stock['Ticker'].lower() == ticker.lower():
            array_found_in = "rsa" if stock in rsa_data else "past"

            if split_ratio:
                stock['Split Ratio'] = split_ratio
                logging.info(f"Split ratio updated for RSA '{ticker}' to '{split_ratio}'. Requested by {ctx.member.display_name}.")
            if date:
                try:
                    parsed_date = datetime.strptime(date, "%m-%d-%Y")
                    formatted_date = parsed_date.strftime("%m-%d-%Y")
                    stock['Date'] = formatted_date
                    logging.info(f"Date updated for RSA '{ticker}' to '{formatted_date}'. Requested by {ctx.member.display_name}.")
                except ValueError:
                    await ctx.send("Invalid date format. Please use 'MM-DD-YYYY'.", ephemeral=True)
                    return
            if agent:
                stock['Transfer Agent'] = agent
                logging.info(f"Transfer Agent updated for RSA '{ticker}' to '{agent}'. Requested by {ctx.member.display_name}.")
            if source:
                stock['Source'] = source
                logging.info(f"Source updated for RSA '{ticker}' to '{source}'. Requested by {ctx.member.display_name}.")
            if comments:
                stock['Comments'] = comments
                logging.info(f"Comments updated for RSA '{ticker}' to '{comments}'. Requested by {ctx.member.display_name}.")
            if tag:
                stock['Tag'] = tag
                logging.info(f"Status updated for RSA '{ticker}' to '{tag}'. Requested by {ctx.member.display_name}.")
            price = get_current_price(ticker)
            if price is not None:
                price = round(price, 2)
            else:
                await ctx.send(f"Failed to fetch price for the ticker: {ticker}. Please try again.", ephemeral=True)
                return
                
            split_ratio_num = float(stock['Split Ratio'].split(":")[1])
            estimated_profit = round(price * split_ratio_num, 2)

            stock['Current Price'] = price
            stock['Estimated Profit'] = estimated_profit
            logging.info(f"Price and estimated profit updated for RSA '{ticker}'. Requested by {ctx.member.display_name}.")
            
            if array_found_in == "rsa":
                write_json_data("rsa", rsa_data)
            else:
                write_json_data("past", past_data)

            if not asyncio.get_event_loop().is_running():
                asyncio.get_event_loop().create_task(update_stock_prices())

            await ctx.send(f"Stock '{ticker}' updated successfully.", ephemeral=True)
            return

    logging.warning(f"RSA '{ticker}' not found. Requested by {ctx.member.display_name}.")
    await ctx.send(f"RSA '{ticker}' not found.", ephemeral=True)


# Brokers
@slash_command(
    name="brokers",
    description="Track sellable shares across brokers",
    options=[
        {
            "name": "ticker",
            "description": "RSA ticker",
            "type": OptionType.STRING,
            "required": True
        },
        {
            "name": "broker",
            "description": "Name of broker",
            "type": OptionType.STRING,
            "required": True,
            "choices": [{"name": "DAILY", "value": "DAILY"}] + [{"name": broker, "value": broker} for broker in BROKERS]
        },
        {
            "name": "status",
            "description": "Status",
            "type": OptionType.INTEGER,
            "required": True,
            "choices": [
                {"name": "Unavailable", "value": 0},
                {"name": "Available", "value": 1}
            ]
        }
    ]
)
async def brokers(ctx: SlashContext, ticker: str, broker: str, status: int):
    ticker = ticker.upper()
    rsa_data = read_json_data("rsa")
    past_data = read_json_data("past")
    
    brokers_to_update = DAILY_BROKERS if broker == "DAILY" else [broker]

    for data in [rsa_data, past_data]:
        for stock in data:
            if stock["Ticker"].upper() == ticker:
                for broker_to_update in brokers_to_update:
                    if broker_to_update not in stock["BrokerTracking"]:
                        continue
                    if stock["BrokerTracking"][broker_to_update] == status:
                        status_text = "Available" if status == 1 else "Unavailable"
                        continue
                    stock["BrokerTracking"][broker_to_update] = status
                write_json_data("rsa" if data is rsa_data else "past", data)
                status_text = "available" if status == 1 else "unavailable"
                await ctx.send(f"${ticker} is {status_text} to sell on {', '.join(brokers_to_update)}!\nThank you {ctx.member.display_name} for contributing, have a :cookie:", ephemeral=False)
                return

    await ctx.send(f"RSA '{ticker}' not found.", ephemeral=True)


# Confirm RSA
@slash_command(
    name="confirm",
    description="Confirm whether an RSA was ROUNDED or CIL. Choose PENDING to move to the RSA Bulletin.",
    options=[
        {
            "name": "ticker",
            "description": "RSA ticker",
            "type": OptionType.STRING,
            "required": True
        },
        {
            "name": "tag",
            "description": "Status of the RSA",
            "type": OptionType.STRING,
            "required": True,
            "choices": [{"name": tag, "value": tag} for tag in TAGS]
        }
    ]
)
async def confirm_stock(ctx: SlashContext, ticker: str, tag: str):
    try:
        stock_data = read_json_data("rsa")
        past_stock_data = read_json_data("past")
        for i, stock in enumerate(stock_data):
            if stock['Ticker'].lower() == ticker.lower():
                removed_stock = stock_data.pop(i)
                removed_stock["Tag"] = tag
                past_stock_data.append(removed_stock)
                write_json_data("rsa", stock_data)
                write_json_data("past", past_stock_data)
                if not asyncio.get_event_loop().is_running():
                    asyncio.get_event_loop().create_task(update_stock_prices())

                logging.info(f"RSA '{ticker}' has been confirmed '{tag}'. Requested by {ctx.member.display_name}.")
                await ctx.send(f"RSA '{ticker}' has been confirmed '{tag}'.", ephemeral=True)
                return

        logging.warning(f"RSA '{ticker}' not found. Requested by {ctx.member.display_name}.")
        await ctx.send(f"RSA '{ticker}' not found.", ephemeral=True)

    except Exception as e:
        logging.error(f"An error occurred while confirming RSA '{ticker}': {e} Requested by {ctx.member.display_name}.")
        await ctx.send(f"An error occurred while confirming RSA '{ticker}'. Please try again.", ephemeral=True)


# Delete RSA
@slash_command(
    name="delete",
    description="Delete RSA from the database",
    options=[
        {
            "name": "ticker",
            "description": "RSA ticker",
            "type": OptionType.STRING,
            "required": True
        }
    ]
)
async def delete_stock(ctx: SlashContext, ticker: str):
    try:
        stock_data = read_json_data("rsa")
        past_stock_data = read_json_data("past")
        research_stock_data = read_json_data("research")
        stock_found = False

        def delete_stock_from_array(stock_array):
            for i, stock in enumerate(stock_array):
                if stock['Ticker'].lower() == ticker.lower():
                    stock_array.pop(i)
                    return True
            return False

        stock_found |= delete_stock_from_array(stock_data)
        stock_found |= delete_stock_from_array(past_stock_data)
        stock_found |= delete_stock_from_array(research_stock_data)

        write_json_data("rsa", stock_data)
        write_json_data("past", past_stock_data)
        write_json_data("research", research_stock_data)

        if stock_found:
            logging.info(f"RSA '{ticker}' deleted successfully. Requested by {ctx.member.display_name}.")
            await ctx.send(f"RSA '{ticker}' deleted successfully.", ephemeral=True)
        else:
            logging.warning(f"RSA '{ticker}' not found. Requested by {ctx.member.display_name}.")
            await ctx.send(f"RSA '{ticker}' not found.", ephemeral=True)

    except Exception as e:
        logging.error(f"An error occurred while deleting RSA '{ticker}': {e} Requested by {ctx.member.display_name}.")
        await ctx.send(f"An error occurred while deleting RSA '{ticker}'. Please try again.", ephemeral=True)


bot.start()
