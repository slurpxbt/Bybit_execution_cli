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

            if "1000000" in symbol:
                symbol = symbol.replace("1000000", "")
            elif "100000" in symbol:
                symbol = symbol.replace("100000", "")
            elif "10000" in symbol:
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
            print("\n")
            print("Current positions:")
            positions_df = pd.DataFrame.from_dict(open_positions, orient="index")
            positions_df = positions_df[["symbol", "side", "size", "positionValue", "avgPrice", "unrealisedPnl", "takeProfit", "stopLoss"]]
            print(positions_df.to_markdown())
            print("\n")

        return open_positions

    else:
        if display:
            print("\n")
            print("No open positions")
            print("\n")
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

def limit_tranche_open(client, usd_size, ticker, side, upper_price, lower_price, order_amount, bid_ask:bool):
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
    if not bid_ask:
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
    else:
        error = False

    if not error:
        single_order = int(usd_size / order_amount)
        price = lower_price
        for i in range(order_amount):
            orders.append([round(single_order / price, decimals), round(price, tick_decimals)])
            price += spacing

        for order in orders:
            client.place_order(category="linear", symbol=ticker, side=side, orderType="Limit", qty=order[0], price=order[1], timeInForce="GTC", reduceOnly=False)
            time.sleep(0.01)


def limit_tranche_close(client, coin_size, ticker, side, upper_price, lower_price, order_amount, bid_ask:bool):
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
    if not bid_ask:
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
    else:
        error = False

    if not error:
        single_order = round(coin_size / order_amount, decimals)
        price = lower_price
        for i in range(order_amount):
            orders.append([round(single_order, decimals), round(price, tick_decimals)])
            price += spacing

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
                print("\n")
                print(f"risk limit would be exceded adjust risk limits or choose lower pos size || risk limit: {position_size_limit}")
                print("\n")
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
        else:
            print("\n")
            print(f"risk limit would be exceded adjust risk limits or choose lower pos size || risk limit: {position_size_limit}")
            print("\n")

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
    ticker = cli_inputs.select_ticker(tickers=tickers, spot=False)

    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()

    market_order_thread = Thread(target=market_order_open, args=(client, ticker, side, usd_size), name=f"FUTURES_{ticker}_{side}_{usd_size}").start()


def set_market_order_close(client):
    """

    :param client:
    :return:
    """

    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    pct = cli_inputs.select_pct()
    coin_size = round(size * pct, decimals)

    market_order_thread = Thread(target=market_order_close, args=(client, ticker, side, coin_size), name=f"FUTURES_{ticker}_{side}_{coin_size}_coins").start()


def set_linear_twap_open(client):
    tickers = get_usdt_futures_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers, spot=False)

    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()
    duration = cli_inputs.select_duration()
    order_amount = cli_inputs.select_order_amount()

    linear_twap_thread = Thread(target=linear_twap_open, args=(client, ticker, side, usd_size, duration, order_amount), name=f"FUTURES_{ticker}_{side}_{usd_size}_twap{round(duration / 60)}min").start()


def set_linear_twap_close(client):
    """

       :param client:
       :return:
       """

    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)

    pct = cli_inputs.select_pct()
    coin_size = round(size * pct, decimals)
    duration = cli_inputs.select_duration()
    order_amount = cli_inputs.select_order_amount()

    linear_twap_thread = Thread(target=linear_twap_close, args=(client, ticker, side, coin_size, duration, order_amount), name=f"FUTURES_{ticker}_{side}_{coin_size}_coins_twap{round(duration / 60)}min").start()


def set_limits_open(client):

    positions = get_open_positions(client, False)

    tickers = get_usdt_futures_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers, spot=False)
    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()
    upper_price = cli_inputs.select_upper_limit_price()
    lower_price = cli_inputs.select_lower_limit_price()
    order_amount = cli_inputs.select_order_amount()
    bid_ask = False
    position_exits = False
    position = None
    for key, value in positions.items():
        if value["symbol"] == ticker:
            position_exits = True
            position = value
            break

    if not position_exits:
        # do you want to place sl ?
        sl_check = 0
        while sl_check not in [1, 2]:
            sl_check = int(input("Do you want to place stoploss ?[1 > yes, 2 > no] >>> "))
            if sl_check in [1, 2]:
                if sl_check == 1:
                    sl_price_ok = False
                    sl_side = None
                    while not sl_price_ok:
                        if side == "b":
                            sl_price = float(input("Choose stoploss price >>> "))
                            try:
                                if sl_price > 0 and sl_price < lower_price:
                                    sl_price_ok = True
                                    sl_side = "Sell"
                                    client.place_order(category="linear", symbol=ticker, side=sl_side, orderType="Market", qty="0", triggerDirection=2, timeInForce="IOC", reduceOnly=True, closeOnTrigger=True, triggerBy="LastPrice", triggerPrice=str(sl_price))
                            except:
                                print("Wrong stoploss input, must be number and lower than lowest limit order")

                        elif side == "s":
                            sl_price = float(input("Choose stoploss price >>> "))
                            try:
                                if sl_price > upper_price:
                                    sl_price_ok = True
                                    sl_side = "Buy"
                                    client.place_order(category="linear", symbol=ticker, side=sl_side, orderType="Market", qty="0", triggerDirection=1, timeInForce="IOC", reduceOnly=True, closeOnTrigger=True, triggerBy="LastPrice", triggerPrice=str(sl_price))
                            except:
                                print("Wrong stoploss input, must be number and higher than highest limit order")
            else:
                print("wrong input, try again")


    limit_open_thread = Thread(target=limit_tranche_open, args=(client, usd_size, ticker, side, upper_price, lower_price, order_amount, bid_ask), name=f"FUTURES_{ticker}_{side}_limit_tranche_{usd_size}").start()


def set_limits_close(client):
    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)
    bid_ask = False
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
        limit_close_thread = Thread(target=limit_tranche_close, args=(client, coin_size, ticker, side, upper_price, lower_price, order_amount, bid_ask), name=f"FUTURES_{ticker}_{side}_limit_tranche_{coin_size}").start()


def set_limits_at_bidask_open(client):
    positions = get_open_positions(client, False)

    tickers = get_usdt_futures_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers, spot=False)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)
    tick_decimals = str(tick_size)[::-1].find('.')

    side = cli_inputs.select_side()
    usd_size = cli_inputs.select_usdt_size()

    bps_range = 0.004
    if ticker in ["BTCUSDT", "ETHUSDT"]:
        bps_range = 0.001
    last_price = get_last_price(client, ticker)

    if side == "b":
        upper_price = last_price
        lower_price = round( upper_price - (last_price * bps_range) ,tick_decimals)
    elif side == "s":
        lower_price = last_price
        upper_price = round(lower_price + (last_price * bps_range), tick_decimals)

    order_amount = 10
    bid_ask = True

    position_exits = False
    position = None
    for key, value in positions.items():
        if value["symbol"] == ticker:
            position_exits = True
            position = value
            break

    if not position_exits:
        # do you want to place sl ?
        sl_check = 0
        while sl_check not in [1, 2]:
            sl_check = int(input("Do you want to place stoploss ?[1 > yes, 2 > no] >>> "))
            if sl_check in [1, 2]:
                if sl_check == 1:
                    sl_price_ok = False
                    sl_side = None
                    while not sl_price_ok:
                        if side == "b":
                            sl_price = float(input("Choose stoploss price >>> "))
                            try:
                                if sl_price > 0 and sl_price < lower_price:
                                    sl_price_ok = True
                                    sl_side = "Sell"
                                    client.place_order(category="linear", symbol=ticker, side=sl_side, orderType="Market", qty="0", triggerDirection=2, timeInForce="IOC", reduceOnly=True, closeOnTrigger=True, triggerBy="LastPrice", triggerPrice=str(sl_price))
                            except:
                                print("Wrong stoploss input, must be number and lower than lowest limit order")

                        elif side == "s":
                            sl_price = float(input("Choose stoploss price >>> "))
                            try:
                                if sl_price > upper_price:
                                    sl_price_ok = True
                                    sl_side = "Buy"
                                    client.place_order(category="linear", symbol=ticker, side=sl_side, orderType="Market", qty="0", triggerDirection=1, timeInForce="IOC", reduceOnly=True, closeOnTrigger=True, triggerBy="LastPrice", triggerPrice=str(sl_price))
                            except:
                                print("Wrong stoploss input, must be number and higher than highest limit order")
            else:
                print("wrong input, try again")

    limit_open_thread = Thread(target=limit_tranche_open, args=(client, usd_size, ticker, side, upper_price, lower_price, order_amount, bid_ask), name=f"FUTURES_{ticker}_{side}_limit_tranche_{usd_size}").start()


def set_limits_at_bidask_close(client):
    close_id, ticker, side, size, usd_value = select_close_id_futures(client)
    max_order_size_coin, min_order_size_coin, decimals, tick_size, position_size_limit = get_instrument_info(client, ticker)
    tick_decimals = str(tick_size)[::-1].find('.')

    bps_range = 0.004
    if ticker in ["BTCUSDT", "ETHUSDT"]:
        bps_range = 0.001


    bid_ask = True
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

    last_price = get_last_price(client, ticker)
    if side == "b":
        upper_price = last_price
        lower_price = round(upper_price - (last_price * bps_range), tick_decimals)
    elif side == "s":
        lower_price = last_price
        upper_price = round(lower_price + (last_price * bps_range), tick_decimals)

    order_amount = 10

    if close:
        limit_close_thread = Thread(target=limit_tranche_close, args=(client, coin_size, ticker, side, upper_price, lower_price, order_amount, bid_ask), name=f"FUTURES_{ticker}_{side}_limit_tranche_{coin_size}").start()


def set_multiple_twaps_open(client):

    exit_ = False

    tickers = get_usdt_futures_tickers(client=client)
    twaps = []
    mode = 0
    while not exit_:
        ticker = cli_inputs.select_ticker(tickers=tickers, spot=False)
        side = cli_inputs.select_side()
        usd_size = cli_inputs.select_usdt_size()
        order_amount = cli_inputs.select_order_amount()
        duration = cli_inputs.select_duration()
        print("\n")

        twaps.append([ticker,side, usd_size, duration, order_amount])
        mode = 0

        while mode not in [1,2]:
            mode = int(input("add another twap/exit [1- another twap, 2-exit] >>> "))
            if mode == 2:
                exit_ = True
            elif mode not in [1,2]:
                print("Wrong input, input must be 1 or 2")

    if twaps:
        print("Executing following twaps:")
        for i in twaps:
            print(f"{i[0]} - {i[1]} - {i[2]} usd - {i[3] / 60}min")

            linear_twap_thread = Thread(target=linear_twap_open, args=(client, i[0], i[1], i[2], i[3], i[4]), name=f"FUTURES_{i[0]}_{i[1]}_{i[2]}_twap{round(i[3] / 60)}min").start()


def set_multiple_twaps_close(client):

    exit_ = False
    mode = 0
    while not exit_:

        set_linear_twap_close(client)
        mode = 0

        while mode not in [1, 2]:
            mode = int(input("add another twap_close/exit [1- another twap, 2-exit] >>> "))
            if mode == 2:
                exit_ = True
            elif mode not in [1, 2]:
                print("Wrong input, input must be 1 or 2")


def close_all_positions(client):
    """
    Function that close all open positions
    :param client:
    :return:
    """

    positions = get_open_positions(client=client, display=False)
    if positions:
        print("Select duration in which you want to close all positions[minutes]")
        duration = cli_inputs.select_duration()
        for close_id in positions.keys():
            position = positions[close_id]
            ticker = position["symbol"]
            side = position["side"]
            coin_size = float(position["size"])
            usd_value = float(position["positionValue"])

            if side == "Buy":
                side_ = "long"
                side = "s"
            elif side == "Sell":
                side_ = "short"
                side = "b"

            if duration > 400:
                if usd_value <= 20000:
                    order_amount = 20
                elif 20000 < usd_value <= 50000:
                    order_amount = 50
                elif 50000 < usd_value <= 100000:
                    order_amount = 100
                elif 100000 < usd_value <= 250000:
                    order_amount = 150
                elif 250000 < usd_value <= 500000:
                    order_amount = 200
                elif 500000 < usd_value <= 1000000:
                    order_amount = 300
                elif usd_value > 1000000:
                    order_amount = 400
            else:
                if usd_value <= 20000:
                    order_amount = 1
                elif 20000 < usd_value <= 50000:
                    order_amount = 3
                elif 50000 < usd_value <= 100000:
                    order_amount = 5
                elif 100000 < usd_value <= 250000:
                    order_amount = 10
                elif 250000 < usd_value <= 500000:
                    order_amount = 15
                elif 500000 < usd_value <= 1000000:
                    order_amount = 30
                elif usd_value > 1000000:
                    order_amount = 45

            print(f"started closing {ticker} {side_} || {coin_size} coins")
            linear_twap_thread = Thread(target=linear_twap_close, args=(client, ticker, side, coin_size, duration, order_amount), name=f"FUTURES_{ticker}_{side}_{coin_size}_coins_twap{round(duration / 60)}min").start()
    else:
        print("\nNo open positions")


def bid_IO_wipe(client):
    """
    Function that sets limits order in prefered % range below from current price >> it's buy only function
    :param client:
    :return:
    """
    tickers = get_usdt_futures_tickers(client=client)
    print("\nSelect % below price where you want to bid > ex: [15-30% below current price]")
    upper_pct = cli_inputs.select_upper_pct()
    lower_pct = cli_inputs.select_lower_pct()

    if upper_pct < lower_pct:
        side = "b"

        exit_ = False

        tickers = get_usdt_futures_tickers(client=client)
        while not exit_:

            ticker = cli_inputs.select_ticker(tickers=tickers, spot=False)
            usd_size = cli_inputs.select_usdt_size()
            last_price = get_last_price(client, ticker)

            upper_price = last_price - (last_price * upper_pct)
            lower_price = last_price - (last_price * lower_pct)

            if usd_size <= 20000:
                order_amount = 10
            elif 20000 < usd_size <= 50000:
                order_amount = 20
            elif 50000 < usd_size <= 100000:
                order_amount = 30
            elif 100000 < usd_size <= 250000:
                order_amount = 40
            elif 250000 < usd_size <= 500000:
                order_amount = 50
            elif usd_size > 500000:
                order_amount = 70


            limit_open_thread = Thread(target=limit_tranche_open, args=(client, usd_size, ticker, side, upper_price, lower_price, order_amount), name=f"FUTURES_{ticker}_{side}_limit_tranche_{usd_size}").start()

            mode = 0
            while mode not in [1,2]:
                mode = int(input("add another coin bids/exit [1- another coin, 2-exit] >>> "))
                if mode == 2:
                    exit_ = True
                elif mode not in [1,2]:
                    print("Wrong input, input must be 1 or 2")
    else:
        print("\nUpper % must be lower number than lower %")



# todo: TESTING
# api_key, api_secret = get_credentials(account="personal")
# client = auth(api_key, api_secret)


# set_limits_at_bidask_open(client)
# set_limits_at_bidask_close(client)


# set_limits_open(client)

# bid_IO_wipe(client)

# close_all_positions(client)

# set_multiple_twaps_open(client)
# set_multiple_twaps_close(client)

# usdt = get_usdt_balance(client)
# tickers = get_usdt_futures_tickers(client)

# set_limits_close(client)
# set_limits_at_avgPrc_close(client)

# set_limits_open(client)
# set_limits_at_avgPrc_open(client)

# set_linear_twap_open(client)
# set_linear_twap_close(client)

# set_market_order_open(client)
# set_market_order_close(client)


# get_instrument_info(client, "BTCUSDT")
# positions = get_open_positions(client, display=True)

# market_order(client, "ETHUSDT", "s", 1000)
# market_close(client, "ETHUSDT", "b", 0.6)

# linear_twap_open(client, "ETHUSDT", "s", 1000, 30, 5)
# linear_twap_close(client, "ETHUSDT", "b", 1000, 30, 5)

# limit_tranche_open(client, 1000, "ETHUSDT", "b", 1770, 1740, 5)
# limit_tranche_close(client, 0.55, "ETHUSDT", "b", 1780, 1740, 5)


# limit_tranche_avg_price_reduce(client, 0.028, "BTCUSDT", "s", 35800, 35500, 35600, 5)