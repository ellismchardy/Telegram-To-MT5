import pandas as pd
from telethon.sync import TelegramClient, events
import asyncio
import re
import MetaTrader5 as mt5
import os
import time
import threading
import logging




# Configuration
name = 'anon'
api_id = '25435383'  
api_hash = '2c2e60b7c143b96c11fcf351746db429'  
chat = 't.me/testingscriptforfxx'
symbol = 'XAUUSD'  

# MT5 Details
login = 1569674  
password = 'U2WMars3h-'  
server = 'ACGMarkets-Live' 

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Track whether a trade has been executed for a specific signal message
trade_executed = {}

# MT5 setup
def mt5_setup():
    logger.info("Initializing MT5...")
    if not mt5.initialize():
        logger.error("initialize() failed, error code = %s", mt5.last_error())
        quit()
    logger.info("MT5 initialized successfully")

    logger.info("Logging into MT5 account...")
    authorized = mt5.login(login, password, server)
    if not authorized:
        logger.error("Failed to connect to account #%s, error code: %s", login, mt5.last_error())
        quit()
    else:
        logger.info("Connected to account #%s", login)

    balance = get_account_balance()
    logger.info("Account Balance: %s", balance)

def mt5_shutdown():
    mt5.shutdown()

def get_account_balance():
    account_info = mt5.account_info()
    if account_info is None:
        logger.error("Failed to get account info, error code = %s", mt5.last_error())
        quit()
    return account_info.balance

def get_current_price(symbol, action):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logger.error("Failed to get current price for %s, error code = %s", symbol, mt5.last_error())
        quit()
    return tick.ask if action.lower() == 'buy' else tick.bid

def calculate_lot_size(symbol, risk_amount, stop_loss_distance):
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        logger.error("Failed to get symbol info for %s", symbol)
        return 0

    tick_value = symbol_info.trade_tick_value
    lot_size = round(risk_amount / (stop_loss_distance * tick_value) / 1000, 2)

    return lot_size

def place_order(symbol, action, current_price, sl, tp, lot_size, message):
    if action.lower() == 'buy':
        order_type = mt5.ORDER_TYPE_BUY
    elif action.lower() == 'sell':
        order_type = mt5.ORDER_TYPE_SELL
    else:
        logger.error("Unknown action: %s", action)
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": current_price,
        "sl": sl,
        "tp": tp,
        "deviation": 0,
        "magic": 234000,
        "comment": "",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result is None:
        logger.error("Order send failed, result is None")
        logger.error("Last error: %s", mt5.last_error())
        return

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error("Order failed, retcode = %s", result.retcode)
    else:
        logger.info("Order placed. Order ID: %s", result.order)
        trade_executed[message] = result.order

        trade_data = {
            'Order ID': result.order,
            'Symbol': symbol,
            'Entry Price': current_price,
            'Take Profit': tp,
            'Stop Loss': sl,
            'Result': 'Open'
        }

        trade_log = pd.DataFrame([trade_data])
        trade_log.to_csv('trade_log.csv', mode='a', header=not os.path.exists('trade_log.csv'), index=False)

        threading.Thread(target=monitor_trade, args=(result.order, current_price, tp, sl, action)).start()

def update_trade_result(order_id, result):
    trade_log = pd.read_csv('trade_log.csv')
    trade_log.loc[trade_log['Order ID'] == order_id, 'Result'] = result
    trade_log.to_csv('trade_log.csv', index=False)

def monitor_trade(order_id, entry_price, tp, sl, action):
    tp_distance = abs(tp - entry_price)
    threshold_price = entry_price + 0.6 * tp_distance if action.lower() == 'buy' else entry_price - 0.6 * tp_distance

    while True:
        current_price = get_current_price(symbol, action)

        if (action.lower() == 'buy' and current_price >= threshold_price) or (action.lower() == 'sell' and current_price <= threshold_price):
            modify_sl_to_breakeven(order_id, entry_price)
            break

        time.sleep(2)

        closed_positions = mt5.history_deals_get(ticket=order_id)
        if closed_positions:
            for deal in closed_positions:
                if deal.position_id == order_id:
                    if deal.price == tp:
                        update_trade_result(order_id, 'W')
                    elif deal.price == sl:
                        update_trade_result(order_id, 'L')
                    else:
                        update_trade_result(order_id, 'BE')
            break

def modify_sl_to_breakeven(order_id, entry_price):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for position in positions:
            if position.ticket == order_id:
                sl_request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": position.ticket,
                    "sl": entry_price,
                    "tp": position.tp,
                    "deviation": 0,
                    "magic": 234000,
                    "comment": ""
                }

                result = mt5.order_send(sl_request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info("Stop loss moved to breakeven for order %s", order_id)
                else:
                    logger.error("Failed to move stop loss to breakeven for order %s, retcode = %s", order_id, result.retcode)
                break


def connection_checker():
    while True:
        if check_mt5_connection():
            print("MT5 connection is working")
        else:
            print("MT5 connection is not working")
        time.sleep(5)


def parse_signal(message):
    match = re.search(r'(Buy|Sell)[\s\S]*TP:\s*([\d.]+)', message)
    if match:
        action, tp = match.groups()
        tp = float(tp)
        return action, tp
    
    match = re.search(r'(Buy|Sell)[\s\S]*TP1\s*([\d.]+)', message)
    if match:
        action, tp = match.groups()
        tp = float(tp)
        return action, tp
    
    match = re.search(r'(Buy|Sell)[\s\S]*TP1:\s*([\d.]+)', message)
    if match:
        action, tp = match.groups()
        tp = float(tp)
        return action, tp
    
    match = re.search(r'(Buy|Sell)[\s\S]*TP\s*([\d.]+)', message)
    if match:
        action, tp = match.groups()
        tp = float(tp)
        return action, tp
    return None, None


def check_mt5_connection():
    if not mt5.initialize():
        logger.error("MT5 initialization failed, error code = %s", mt5.last_error())
        return False
    authorized = mt5.login(login, password, server)
    if not authorized:
        logger.error("Failed to connect to MT5 account #%s, error code = %s", login, mt5.last_error())
        return False
    logger.info("Connection to MT5 verified successfully")
    return True


async def main():
    mt5_setup()

    connection_thread = threading.Thread(target=connection_checker, daemon=True)
    connection_thread.start()

    async with TelegramClient(name, api_id, api_hash) as client:
        @client.on(events.NewMessage(chats=chat))
        async def handler(event):
            message = event.message.message
            if 'Prepare' in message:
                if check_mt5_connection():
                    logger.info("MT5 connection is working and ready to accept trades.")
                else:
                    logger.error("MT5 connection is not working.")
            if ('Ready Signal!' in message or 'TP1' in message) and message not in trade_executed:
                action, tp = parse_signal(message)
                if action and tp:
                    logger.info("New signal received...")

                    balance = get_account_balance()
                    risk_amount = balance * 0.0025
                    current_price = get_current_price(symbol, action)

                    rrr = 1
                    stop_loss_distance = abs(current_price - tp) / rrr
                    sl = current_price - stop_loss_distance if action.lower() == 'buy' else current_price + stop_loss_distance

                    lot_size = calculate_lot_size(symbol, risk_amount, stop_loss_distance)

                    place_order(symbol, action, current_price, sl, tp, lot_size, message)
                else:
                    logger.warning("No valid signal found in the message.")

        logger.info("Listening for new messages in %s...", chat)
        await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())