import traceback
from pybit.unified_trading import HTTP
import time
import pandas as pd
import json
from pathlib import Path
from dhooks import Webhook
import cli_inputs
from threading import Thread


def get_credentials(account):
    root = Path(".")
    file_path = f"{root}/credentials.json"

    with open(file_path) as file:

        file = file.read()
        credentials = json.loads(file)

        api_key = credentials[account]["bybit_api_key"]
        api_secret = credentials[account]["bybit_secret_key"]

    return api_key, api_secret


def auth(api_key, api_secret):
    bybit_client = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

    return bybit_client


def get_usdt_balance(client):
    balances = client.get_wallet_balance(accountType="UNIFIED")["result"]["list"][0]["coin"]
    usdt_balance = None
    for balance in balances:
        if balance["coin"] == "USDT":
            usdt_balance = round(float(balance["equity"]))
            print(f"total usdt balance: {usdt_balance} USDT")

    if usdt_balance is not None:
        return usdt_balance
    else:
        print("no usdt available")


def get_usdt_futures_tickers(client):
    symbols = client.get_instruments_info(category="linear")["result"]["list"]
    tickers = {}
    for row in symbols:
        symbol = row["symbol"]
        ticker = row["symbol"]
        if "USDT" in symbol:

            symbol = symbol.replace("USDT", "")

            if "10000" in symbol:
                symbol = symbol.replace("10000", "")
            elif "1000" in symbol:
                symbol = symbol.replace("1000", "")

            tickers[symbol] = ticker

    return tickers


def get_instrument_info(client, ticker):
    """
    Gives instrument data for size, risk limits, etc

    :param client: bybit client
    :param ticker: ticker
    :return:
    """
    instrument_info = client.get_instruments_info(category="linear", symbol=ticker)["result"]["list"][0]
    risk_limit_info = client.get_risk_limit(category="linear", symbol=ticker)["result"]["list"][0]

    position_size_limit = int(risk_limit_info["riskLimitValue"]) # USDT

    min_order_size_coin = float(instrument_info["lotSizeFilter"]["minOrderQty"])    # coin
    max_order_size_coin = float(instrument_info["lotSizeFilter"]["maxOrderQty"])    # coin

    decimals = str(str(instrument_info["lotSizeFilter"]["minOrderQty"]))[::-1].find('.')

    tick_size = instrument_info["priceFilter"]["tickSize"]

    return max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit


def get_last_price(client, ticker):
    ticker_data = client.get_tickers(category="linear", symbol=ticker)["result"]["list"][0]
    last_price = float(ticker_data["lastPrice"])
    return last_price

# ORDER/POSITION OVERVIEW FUNCTIONS
def get_open_positions(client, display:bool):
    """
    Gives you all open USDT-Futures positions

    :param client: bybit client
    :param display: True = displays all positions into dataframe, False = doesn't display positions
    :return:
    """
    positions = client.get_positions(category="linear", settleCoin="USDT")["result"]["list"]
    open_positions = {}
    counter = 0
    for position in positions:
        size = float(position["size"])

        if size > 0:
            open_positions[counter] = position
            counter += 1

    if open_positions:
        if display:
            print("Current positions:")
            positions_df = pd.DataFrame.from_dict(open_positions, orient="index")
            positions_df = positions_df[["symbol", "side", "size", "positionValue", "avgPrice", "unrealisedPnl", "takeProfit", "stopLoss"]]
            print(positions_df.to_markdown())

        return open_positions

    else:
        if display:
            print("No open positions")
        return open_positions


def set_position_sl_tp(client):
    positions = get_open_positions(client=client, display=True)
    try:
        modify_id = int(input("select ID of the position you wish to modify >>> "))
    except:
        modify_id = None
        print("Error: ID must be number")


    try:
        print("What do you want to modify: 1=tp/sl, 2=tp, 3=sl")
        modify_type = int(input("Input the modification type you want[1, 2, 3] >>>"))
    except:
        modify_type = None
        print("Error: Modification type must me number")

    if modify_type is not None and modify_id is not None:
        if modify_id in positions.keys():

            position = positions[modify_id]
            ticker = position["symbol"]
            position_side = position["side"]

            takeProfit = position["takeProfit"]
            stopLoss = position["stopLoss"]

            last_price = get_last_price(client, ticker)
            print(f"{ticker} selected to modify")

            if position_side == "Buy":
                if modify_type == 1:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price < last_price and new_tp_price != 0:
                            print("TP price below last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price
                    except:
                        print("TP price should be number")

                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price > last_price:
                            print("SL price above last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price
                    except:
                        print("SL price should be number")

                    if new_tp_price is not None or new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice",stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP and SL modified >>> new TP: {takeProfit} | new SL: {stopLoss}")
                    else:
                        print("no modifications were made")

                elif modify_type == 2:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price < last_price and new_tp_price != 0:
                            print("TP price below last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price
                    except:
                        print("TP price should be number")

                    if new_tp_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP modified >>> new TP: {takeProfit}")
                    else:
                        print("no modifications were made")

                elif modify_type == 3:
                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price > last_price:
                            print("SL price above last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price

                    except:
                        print("SL price should be number")

                    if new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} SL modified >>> new TP: {stopLoss}")
                    else:
                        print("no modifications were made")

            elif position_side == "Sell":
                if modify_type == 1:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price > last_price:
                            print("TP price above last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price
                    except:
                        print("TP price should be number")

                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price < last_price and new_sl_price != 0:
                            print("SL price below last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price

                    except:
                        print("SL price should be number")

                    if new_tp_price is not None or new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP and SL modified >>> new TP: {takeProfit} | new SL: {stopLoss}")
                    else:
                        print("no modifications were made")

                elif modify_type == 2:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price > last_price:
                            print("TP price above last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price

                    except:
                        print("TP price should be number")

                    if new_tp_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP modified >>> new TP: {takeProfit}")
                    else:
                        print("no modifications were made")

                elif modify_type == 3:
                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price < last_price and new_sl_price != 0:
                            print("SL price below last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price

                    except:
                        print("SL price should be number")

                    if new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} SL modified >>> new TP: {stopLoss}")
                    else:
                        print("no modifications were made")

            else:
                print("ID not found in positions")


# market orders


def market_order_open(client, ticker, side, usd_size):
    """

    this order will split ur size into 20 equal orders and rapid execute them in 0.25s time intervals

    :param client: bybit client
    :param ticker: ticker
    :param side: b > buy, s > sell
    :param usd_size: position size in usdt
    :return:
    """

    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    orders = []
    error = True
    if side == "b":
        side = "Buy"
        error = False
    elif side == "s":
        side = "Sell"
        error = False
    else:
        print(f"Error with side input || input: {side} || should be: b/s")

    if not error:
        last_price = get_last_price(client, ticker)
        coins_to_execute = round(usd_size / last_price, decimals)

        single_order = round(coins_to_execute / 20, decimals)
        if single_order > min_order_size_coin:
            if single_order < max_order_size_coin:
                for i in range(20):
                    orders.append(single_order)
            else:
                print(f"single order to big to execute twap || order size: {single_order} || max order size: {max_order_size_coin} ")
        else:
            print(f"total twap size to low: {usd_size}$")

        time_delay = 0.25
        for order in orders:
            client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC", reduceOnly=False)
            time.sleep(time_delay)


def market_order_close(client, ticker, side, coin_size):
    """
        this order will split ur size into 20 equal orders and rapid execute them in 0.25s time intervals, orders are reduce only

        :param client: bybit client
        :param ticker: ticker
        :param side: b > buy, s > sell
        :param usd_size: position size in usdt
        :return:
        """

    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    orders = []
    error = True
    if side == "b":
        side = "Buy"
        error = False
    elif side == "s":
        side = "Sell"
        error = False
    else:
        print(f"Error with side input || input: {side} || should be: b/s")

    if not error:
        single_order = round(coin_size / 20, decimals)
        if single_order > min_order_size_coin:
            if single_order < max_order_size_coin:
                for i in range(20):
                    orders.append(single_order)
            else:
                print(f"single order to big to execute twap || order size: {single_order} || max order size: {max_order_size_coin} ")
        else:
            print(f"total twap size to low: {coin_size} coins")

        time_delay = 0.1
        for order in orders:
            loop_start = time.time()
            position_size = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"]

            if order > float(position_size):
                order = float(position_size)
                client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC", reduceOnly=True)
                break

            client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC", reduceOnly=True)

            loop_end = time.time()
            if loop_end - loop_start > time_delay:
                pass
            else:
                interval = time_delay - (loop_end - loop_start)
                time.sleep(interval)


def linear_twap_open(client, ticker, side, usd_size, duration, order_amount):
    """
        fuction that split order into equal sized orders and executes them over specified duration with equal time delays
        :param client: bybit client
        :param usd_size: size in usd
        :param ticker: choose ticker
        :param side: b > buy, s > sell
        :param duration: in seconds
        :param order_amount: amount of orders [default: 100 orders, int: specific number of orders)
        :return:
    """

    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    orders = []
    error = True
    if side == "b":
        side = "Buy"
        error = False
    elif side == "s":
        side = "Sell"
        error = False
    else:
        print(f"Error with side input || input: {side} || should be: b/s")

    if not error:
        if order_amount == "default":
            single_order = round(usd_size / 100)
            for i in range(100):
                orders.append(single_order)
        else:
            single_order = round(usd_size / order_amount)
            for i in range(order_amount):
                orders.append(single_order)

        time_delay = duration / order_amount # seconds

        for order in orders:
            loop_start = time.time()
            last_price = get_last_price(client, ticker)
            order = round(order / last_price, decimals)
            if order > min_order_size_coin:
                if order < max_order_size_coin:
                    client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC", reduceOnly=False)
                else:
                    print(f"order to big tp execute || order: {order} || max order: {max_order_size_coin}")
                    break
            else:
                print(f"order to low to be able to execute || order: {order} || min order: {min_order_size_coin}")
                break

            loop_end = time.time()
            if loop_end - loop_start > time_delay:
                pass
            else:
                interval = time_delay - (loop_end - loop_start)
                time.sleep(interval)


def linear_twap_close(client, ticker, side, coin_size, duration, order_amount):
    """
            fuction that split order into equal sized orders and executes them over specified duration with equal time delays
            :param client: bybit client
            :param usd_size: size in usd
            :param ticker: choose ticker
            :param side: b > buy, s > sell
            :param duration: in seconds
            :param order_amount: amount of orders [default: 100 orders, int: specific number of orders)
            :return:
        """
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    orders = []
    error = True
    if side == "b":
        side = "Buy"
        error = False
    elif side == "s":
        side = "Sell"
        error = False
    else:
        print(f"Error with side input || input: {side} || should be: b/s")

    if not error:
        single_order = round(coin_size / order_amount, decimals)
        if single_order > min_order_size_coin:
            if single_order < max_order_size_coin:
                for i in range(order_amount):
                    orders.append(single_order)
            else:
                print(f"single order to big to execute twap || order size: {single_order} || max order size: {max_order_size_coin} ")
        else:
            print(f"total twap size to low: {coin_size} coins")

        time_delay = duration / order_amount  # seconds

        for order in orders:
            loop_start = time.time()
            last_price = get_last_price(client, ticker)
            order = round(order, decimals)
            if order > min_order_size_coin:
                if order < max_order_size_coin:
                    position_size = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"]

                    if order > float(position_size):
                        order = float(position_size)
                        client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC", reduceOnly=True)
                        break

                    client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC", reduceOnly=True)

                else:
                    print(f"order to big tp execute || order: {order} || max order: {max_order_size_coin}")
                    break
            else:
                print(f"order to low to be able to execute || order: {order} || min order: {min_order_size_coin}")
                break

            loop_end = time.time()
            if loop_end - loop_start > time_delay:
                pass
            else:
                interval = time_delay - (loop_end - loop_start)
                time.sleep(interval)


# limit oders

def limit_tranche_open(client, usd_size, ticker, side, upper_price, lower_price, order_amount):
    """

    :param client: bybit client
    :param usd_size: total size
    :param ticker: ticker
    :param side: b > buy, s > sell
    :param upper_price:  upper bound for limit orders
    :param lower_price:  lower bound for limit orders
    :return:
    """

    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)
    tick_decimals = str(tick_size)[::-1].find('.')
    orders = []

    # Calculate the spacing between orders
    spacing = (upper_price - lower_price) / (order_amount)
    last_price = get_last_price(client, ticker)
    if side == "b":
        side = "Buy"
    elif side == "s":
        side = "Sell"

    error = True
    if upper_price > lower_price:
        if side == "Buy":
            if last_price > upper_price:
                error = False
            else:
                print("on buy side last price should be higher than upper price limit")
        elif side == "Sell":
            if last_price < lower_price:
                error = False
            else:
                print("on sell side last price should be lower than lower price limit")
        else:
            print(f"Error with side input || input: {side} || should be: b/s")
    else:
        print("upper price limit should be higher than lower price limit")

    if not error:
        single_order = int(usd_size / order_amount)
        price = lower_price
        for i in range(order_amount):
            orders.append([round(single_order / price, decimals), round(price, tick_decimals)])
            price += spacing

        for order in orders:
            client.place_order(category="linear", symbol=ticker, side=side, orderType="Limit", qty=order[0], price=order[1], timeInForce="GTC", reduceOnly=False)
            time.sleep(0.01)


def limit_tranche_close(client, coin_size, ticker, side, upper_price, lower_price, order_amount):
    """

    :param client: bybit client
    :param usd_size: total size
    :param ticker: ticker
    :param side: b > buy, s > sell
    :param upper_price:  upper bound for limit orders
    :param lower_price:  lower bound for limit orders
    :return:
    """

    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)
    tick_decimals = str(tick_size)[::-1].find('.')
    orders = []

    # Calculate the spacing between orders
    spacing = (upper_price - lower_price) / (order_amount)
    last_price = get_last_price(client, ticker)
    if side == "b":
        side = "Buy"
    elif side == "s":
        side = "Sell"

    error = True
    if upper_price > lower_price:
        if side == "Buy":
            if last_price > upper_price:
                error = False
            else:
                print("on buy side last price should be higher than upper price limit")
        elif side == "Sell":
            if last_price < lower_price:
                error = False
            else:
                print("on sell side last price should be lower than lower price limit")
        else:
            print(f"Error with side input || input: {side} || should be: b/s")
    else:
        print("upper price limit should be higher than lower price limit")

    if not error:
        single_order = round(coin_size / order_amount, decimals)
        price = lower_price
        for i in range(order_amount):
            orders.append([round(single_order, decimals), round(price, tick_decimals)])
            price += spacing

        for order in orders:
            client.place_order(category="linear", symbol=ticker, side=side, orderType="Limit", qty=order[0], price=order[1], timeInForce="GTC", reduceOnly=True)
            time.sleep(0.01)


def limit_tranche_avg_price_open(client, usd_size, ticker, side, upper_price, lower_price, avg_price, order_amount):
    """

    :param client: bybit client
    :param usd_size: total size in usd
    :param ticker: ticker
    :param side: b > buy, s > sell
    :param upper_price: upper price limit
    :param lower_price: lower price limit
    :param avg_price: avg price if all orders filled
    :param order_amount: number of orders
    :return:
    """

    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)
    tick_decimals = str(tick_size)[::-1].find('.')
    orders = []

    last_price = get_last_price(client, ticker)
    if side == "b":
        side = "Buy"
    elif side == "s":
        side = "Sell"

    error = True
    if upper_price > lower_price:
        if side == "Buy":
            if last_price > upper_price:
                if lower_price < avg_price < upper_price:
                    error = False
                else:
                    print("avg price must be between lower and upper limit price")
            else:
                print("on buy side last price should be higher than upper price limit")
        elif side == "Sell":
            if last_price < lower_price:
                if lower_price < avg_price < upper_price:
                    error = False
                else:
                    print("avg price must be between lower and upper limit price")
            else:
                print("on sell side last price should be lower than lower price limit")
        else:
            print(f"Error with side input || input: {side} || should be: b/s")

    else:
        print("upper price limit should be higher than lower price limit")

    if not error:
        # Calculate the spacing between prices using the cubic formula
        a = 4 * (avg_price - lower_price) / ((order_amount - 1) ** 3)
        b = -6 * (avg_price - lower_price) / ((order_amount - 1) ** 2)
        c = 4 * (avg_price - lower_price) / (order_amount - 1)

        price_spacing = lambda i: a * (i ** 3) + b * (i ** 2) + c * i + lower_price

        # Generate limit orders
        usd_size_left = usd_size
        current_avg_price = 0.0

        for i in range(order_amount):
            price = price_spacing(i)
            amount = usd_size / order_amount

            if price > upper_price:
                price = upper_price

            order = (round(amount / price, decimals), round(price, tick_decimals))
            orders.append(order)

            current_avg_price = ((avg_price * (usd_size - amount)) + (price * amount)) / usd_size
            usd_size_left -= amount

        # Adjust the last order to reach the desired average price
        last_order = orders[-1]
        last_amount, last_price = last_order
        price_diff = avg_price - current_avg_price
        last_order = (round(last_amount, decimals), round(last_price + price_diff, tick_decimals))
        orders[-1] = last_order

        for order in orders:
            client.place_order(category="linear", symbol=ticker, side=side, orderType="Limit", qty=order[0], price=order[1], timeInForce="GTC", reduceOnly=False)
            time.sleep(0.01)


def limit_tranche_avg_price_close(client, coin_size, ticker, side, upper_price, lower_price, avg_price, order_amount):
    """

    :param client: bybit client
    :param coin_size: total size in coins
    :param ticker: ticker
    :param side: b > buy, s > sell
    :param upper_price: upper price limit
    :param lower_price: lower price limit
    :param avg_price: avg price if all orders filled
    :param order_amount: number of orders
    :return:
    """

    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)
    tick_decimals = str(tick_size)[::-1].find('.')
    orders = []

    last_price = get_last_price(client, ticker)
    if side == "b":
        side = "Buy"
    elif side == "s":
        side = "Sell"

    error = True
    if upper_price > lower_price:
        if side == "Buy":
            if last_price > upper_price:
                if lower_price < avg_price < upper_price:
                    error = False
                else:
                    print("avg price must be between lower and upper limit price")
            else:
                print("on buy side last price should be higher than upper price limit")
        elif side == "Sell":
            if last_price < lower_price:
                if lower_price < avg_price < upper_price:
                    error = False
                else:
                    print("avg price must be between lower and upper limit price")
            else:
                print("on sell side last price should be lower than lower price limit")
        else:
            print(f"Error with side input || input: {side} || should be: b/s")
    else:
        print("upper price limit should be higher than lower price limit")

    if not error:
        # Calculate the spacing between prices using the cubic formula
        a = 4 * (avg_price - lower_price) / ((order_amount - 1) ** 3)
        b = -6 * (avg_price - lower_price) / ((order_amount - 1) ** 2)
        c = 4 * (avg_price - lower_price) / (order_amount - 1)

        price_spacing = lambda i: a * (i ** 3) + b * (i ** 2) + c * i + lower_price

        # Generate limit orders
        coin_size_left = coin_size
        current_avg_price = 0.0

        for i in range(order_amount):
            price = price_spacing(i)
            amount = coin_size / order_amount

            if price > upper_price:
                price = upper_price

            order = (round(amount, decimals), round(price, tick_decimals))
            orders.append(order)

            current_avg_price = ((avg_price * (coin_size - amount)) + (price * amount)) / coin_size
            coin_size_left -= amount

        # Adjust the last order to reach the desired average price
        last_order = orders[-1]
        last_amount, last_price = last_order
        price_diff = avg_price - current_avg_price
        last_order = (round(last_amount, decimals), round(last_price + price_diff, tick_decimals))
        orders[-1] = last_order

        for order in orders:
            client.place_order(category="linear", symbol=ticker, side=side, orderType="Limit", qty=order[0], price=order[1], timeInForce="GTC", reduceOnly=True)
            time.sleep(0.01)


# risk limit check
def check_risk_limit(client, ticker, usd_size, side):

    risk_ok = False
    position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
    position_size_limit = float(position["riskLimitValue"])
    curr_pos_size_coins = float(position["size"])

    if curr_pos_size_coins > 0:
        if position["side"] == "Buy" and side == "b":
            new_total_size = float(position["positionValue"]) + usd_size
            if new_total_size < position_size_limit:
                risk_ok = True
            else:
                print(f"risk limit would be exceded adjust risk limits or choose lower pos size || risk limit: {position_size_limit}")
        elif position["side"] == "Sell" and side == "s":
            new_total_size = float(position["positionValue"]) + usd_size
            if new_total_size < position_size_limit:
                risk_ok = True
        else:
            if usd_size < position_size_limit:
                risk_ok = True
    else:
        if usd_size < position_size_limit:
            risk_ok = True

    return risk_ok


def select_close_id_futures(client):
    positions = get_open_positions(client=client, display=True)

    try:

        while True:
            close_id = int(input("select ID of the position you wish to close >>> "))

            if close_id in positions.keys():
                position = positions[close_id]
                ticker = position["symbol"]
                side = position["side"]
                size = float(position["size"])
                usd_value = float(position["positionValue"])

                if side == "Buy":
                    side = "s"
                elif side == "Sell":
                    side = "b"

                return close_id, ticker, side, size, usd_value
            else:
                print("Wrong ID selected")
    except:
        print("Error: ID must be number")


def set_market_order_open(client):
    """

    :param client:
    :return:
    """

    tickers = get_usdt_futures_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers)

    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()

    risk_ok = check_risk_limit(client=client, ticker=ticker, usd_size=usd_size, side=side)

    if risk_ok:
        market_order_thread = Thread(target=market_order_open, args=(client, ticker, side, usd_size), name=f"FUTURES_{ticker}_{side}_{usd_size}").start()


def set_market_order_close(client):
    """

    :param client:
    :return:
    """

    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    close = False
    close_by = input("close by: usd size or % [1-usd, 2-%] >>> ")
    if int(close_by) == 1:
        usd_size = cli_inputs.select_usdt_size()
        last_price = get_last_price(client, ticker)
        coin_size = round(usd_size / last_price, decimals)
        close = True
    elif int(close_by) == 2:
        pct = cli_inputs.select_pct()
        coin_size = round(size * pct, decimals)
        close = True
    else:
        print("Wrong input should be 1 or 2")

    if close:
        market_order_thread = Thread(target=market_order_close, args=(client, ticker, side, coin_size), name=f"FUTURES_{ticker}_{side}_{coin_size}_coins").start()


def set_linear_twap_open(client):
    tickers = get_usdt_futures_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers)

    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()
    duration = cli_inputs.select_duration()
    order_amount = cli_inputs.select_order_amount()

    risk_ok = check_risk_limit(client=client, ticker=ticker, usd_size=usd_size, side=side)

    if risk_ok:
        linear_twap_thread = Thread(target=linear_twap_open, args=(client, ticker, side, usd_size, duration, order_amount), name=f"FUTURES_{ticker}_{side}_{usd_size}_twap{round(duration / 60, 1)}min").start()


def set_linear_twap_close(client):
    """

       :param client:
       :return:
       """

    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    close = False
    close_by = input("close by: usd size or % [1-usd, 2-%] >>> ")
    if int(close_by) == 1:
        usd_size = cli_inputs.select_usdt_size()
        last_price = get_last_price(client, ticker)
        coin_size = round(usd_size / last_price, decimals)
        close = True
    elif int(close_by) == 2:
        pct = cli_inputs.select_pct()
        coin_size = round(size * pct, decimals)
        close = True
    else:
        print("Wrong input should be 1 or 2")

    duration = cli_inputs.select_duration()
    order_amount = cli_inputs.select_order_amount()

    if close:
        linear_twap_thread = Thread(target=linear_twap_close, args=(client, ticker, side, coin_size, duration, order_amount), name=f"FUTURES_{ticker}_{side}_{coin_size}_coins_twap{round(duration / 60, 1)}min").start()


def set_limits_open(client):
    tickers = get_usdt_futures_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers)
    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()
    upper_price = cli_inputs.select_upper_limit_price()
    lower_price = cli_inputs.select_lower_limit_price()
    order_amount = cli_inputs.select_order_amount()

    risk_ok = check_risk_limit(client=client, ticker=ticker, usd_size=usd_size, side=side)

    if risk_ok:
        limit_open_thread = Thread(target=limit_tranche_avg_price_open, args=(client, usd_size, ticker, side, upper_price, lower_price ,order_amount), name=f"FUTURES_{ticker}_{side}_limit_tranche_{usd_size}").start()


def set_limits_close(client):
    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    close = False
    while not close:
        close_by = input("close by: usd size or % [1-usd, 2-%] >>> ")
        if int(close_by) == 1:
            usd_size = cli_inputs.select_usdt_size()
            last_price = get_last_price(client, ticker)
            coin_size = round(usd_size / last_price, decimals)
            close = True
        elif int(close_by) == 2:
            pct = cli_inputs.select_pct()
            coin_size = round(size * pct, decimals)
            close = True
        else:
            print("Wrong input should be 1 or 2")

    upper_price = cli_inputs.select_upper_limit_price()
    lower_price = cli_inputs.select_lower_limit_price()
    order_amount = cli_inputs.select_order_amount()

    if close:
        limit_close_thread = Thread(target=limit_tranche_close, args=(client, coin_size, ticker, side, upper_price, lower_price, order_amount), name=f"FUTURES_{ticker}_{side}_limit_tranche_{coin_size}").start()


def set_limits_at_avgPrc_open(client):
    tickers = get_usdt_futures_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers)
    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()
    upper_price = cli_inputs.select_upper_limit_price()
    lower_price = cli_inputs.select_lower_limit_price()
    avg_price = cli_inputs.select_avg_limit_price()
    order_amount = cli_inputs.select_order_amount()

    risk_ok = check_risk_limit(client=client, ticker=ticker, usd_size=usd_size, side=side)

    if risk_ok:
        limit_open_thread = Thread(target=limit_tranche_avg_price_open, args=(client, usd_size, ticker, side, upper_price, lower_price,avg_price ,order_amount), name=f"FUTURES_{ticker}_{side}_limit_tranche_{usd_size}").start()


def set_limits_at_avgPrc_close(client):
    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    close = False
    while not close:
        close_by = input("close by: usd size or % [1-usd, 2-%] >>> ")
        if int(close_by) == 1:
            usd_size = cli_inputs.select_usdt_size()
            last_price = get_last_price(client, ticker)
            coin_size = round(usd_size / last_price, decimals)
            close = True
        elif int(close_by) == 2:
            pct = cli_inputs.select_pct()
            coin_size = round(size * pct, decimals)
            close = True
        else:
            print("Wrong input should be 1 or 2")

    upper_price = cli_inputs.select_upper_limit_price()
    lower_price = cli_inputs.select_lower_limit_price()
    avg_price = cli_inputs.select_avg_limit_price()
    order_amount = cli_inputs.select_order_amount()

    if close:
        limit_close_thread = Thread(target=limit_tranche_avg_price_close, args=(client, coin_size, ticker, side, upper_price, lower_price, avg_price ,order_amount), name=f"FUTURES_{ticker}_{side}_limit_tranche_{coin_size}").start()

