Overview

This project is a trading bot that integrates with Telegram and MetaTrader 5 (MT5). The bot listens for trading signals in a specified Telegram chat, parses the signals, and places orders on the MT5 platform based on the signals received. It also monitors the trades and updates the trade log accordingly.
Features

    Connects to MetaTrader 5 for executing trades.
    Listens for trading signals from a Telegram chat.
    Parses trading signals to determine the action (buy/sell) and target price.
    Places and manages trades, including adjusting stop-loss and take-profit levels.
    Logs trades and their outcomes to a CSV file.
    Monitors and ensures the MT5 connection is active.

Prerequisites

    Python 3.7 or higher
    An MT5 account with valid login credentials
    Telegram API credentials (API ID and API Hash)
    python-dotenv, telethon, MetaTrader5, pandas

Installation

    Clone the repository:

    bash

git clone https://github.com/your-repo/trading-bot.git
cd trading-bot

Install the required Python packages:

bash

pip install -r requirements.txt

Create a .env file in the root directory and add your configuration:

makefile

    NAME=anon
    API_ID=your_api_id
    API_HASH=your_api_hash
    CHAT=your_telegram_chat_name
    SYMBOL=XAUUSD.raw

    MT5_LOGIN=your_mt5_login
    MT5_PASSWORD=your_mt5_password
    MT5_SERVER=your_mt5_server

Usage

    Run the script:

    bash

    python trading_bot.py

    Bot Actions:
        The bot will initialize and connect to MT5.
        It will start listening to the specified Telegram chat for trading signals.
        Upon receiving a valid signal, the bot will place a trade on MT5.
        It will monitor the trade and log its status in trade_log.csv.

Code Breakdown

    Configuration and Setup:
    The bot loads configuration details from the .env file and sets up logging.

    MT5 Functions:
        mt5_setup(): Initializes and logs into the MT5 account.
        mt5_shutdown(): Shuts down the MT5 connection.
        get_account_balance(): Retrieves the current account balance.
        get_current_price(symbol, action): Gets the current price for a given symbol and action.
        calculate_lot_size(symbol, risk_amount, stop_loss_distance): Calculates the lot size for a trade.
        place_order(symbol, action, current_price, sl, tp, lot_size, message): Places an order on MT5.
        update_trade_result(order_id, result): Updates the trade log with the result of a trade.
        monitor_trade(order_id, entry_price, tp, sl, action): Monitors the trade and adjusts stop-loss as necessary.
        modify_sl_to_breakeven(order_id, entry_price): Modifies the stop-loss to the breakeven point.
        connection_checker(): Periodically checks the MT5 connection.

    Signal Parsing:
        parse_signal(message): Parses trading signals from a Telegram message.

    Telegram Client:
        main(): Sets up the Telegram client, listens for new messages, and handles incoming trading signals.

Logging

The bot uses Python's logging library to log important events and errors. Logs are displayed in the console and provide information about the bot's operations and any issues encountered.
Contribution

Contributions are welcome. Please fork the repository and create a pull request with your changes.
License

This project is licensed under the MIT License. See the LICENSE file for details.