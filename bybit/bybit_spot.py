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
            # print(f"total usdt balance: {usdt_balance} USDT")

    if usdt_balance is not None:
        return usdt_balance
    else:
        print("no usdt available")


def get_coin_balance(client, ticker):
    ticker = ticker.replace("USDT", "")
    balances = client.get_wallet_balance(accountType="UNIFIED")["result"]["list"][0]["coin"]
    coin_balance = 0
    usd_value = 0
    for balance in balances:
        if balance["coin"] == ticker:
            coin_balance = float(balance["equity"])
            usd_value = round(float(balance["usdValue"]),2)

    if coin_balance and usd_value > 1:
        # print(f"total {ticker} balance: {coin_balance} || usd value: {usd_value}")
        return coin_balance, usd_value
    else:
        print(f"no spot positions found for: {ticker}")
        return coin_balance, usd_value


def get_spot_usdt_tickers(client):
    symbols = client.get_instruments_info(category="spot")["result"]["list"]
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
    instrument_info = client.get_instruments_info(category="spot", symbol=ticker)["result"]["list"][0]

    min_order_size_coin = float(instrument_info["lotSizeFilter"]["minOrderQty"])    # coin
    max_order_size_coin = float(instrument_info["lotSizeFilter"]["maxOrderQty"])    # coin

    min_order_size_usd = int(instrument_info["lotSizeFilter"]["minOrderAmt"]) # usdt
    max_order_size_usd = int(instrument_info["lotSizeFilter"]["maxOrderAmt"]) # usdt

    decimals = str(str(instrument_info["lotSizeFilter"]["minOrderQty"]))[::-1].find('.')

    tick_size = instrument_info["priceFilter"]["tickSize"]

    return max_order_size_coin, min_order_size_coin, min_order_size_usd, max_order_size_usd, decimals, tick_size


def get_last_price(client, ticker):
    ticker_data = client.get_tickers(category="spot", symbol=ticker)["result"]["list"][0]
    last_price = float(ticker_data["lastPrice"])
    return last_price


def get_all_spot_positions(client):
    balances = client.get_wallet_balance(accountType="UNIFIED")["result"]["list"][0]["coin"]

    spot_positions = []

    for balance in balances:
        coin = balance["coin"]
        usd_value = round(float(balance["usdValue"]))
        coins = float(balance["walletBalance"])

        if usd_value > 10:
            spot_positions.append([coin, usd_value, coins])

    if spot_positions:
        print("\n")
        print("Current spot positions")
        positions_df = pd.DataFrame(spot_positions, columns=["coin", "usdValue", "coinAmount"])
        positions_df["coinAmount"] = positions_df["coinAmount"].astype(str)
        print(positions_df.to_markdown(floatfmt=''))
        print("\n")
    else:
        print("No spot positions")



# order functions
# limit orders
# limit
def limit_tranche(client, usd_size, ticker, side, upper_price, lower_price, order_amount):
    """

    :param client: bybit client
    :param usd_size: total size
    :param ticker: ticker
    :param side: b > buy, s > sell
    :param upper_price:  upper bound for limit orders
    :param lower_price:  lower bound for limit orders
    :return:
    """

    if order_amount == "default":
        order_amount = 15

    max_order_size_coin, min_order_size_coin, min_order_size_usd, max_order_size_usd, decimals, tick_size = get_instrument_info(client, ticker)
    tick_decimals = str(tick_size)[::-1].find('.')
    orders = []

    # Calculate the spacing between orders
    spacing = (upper_price - lower_price) / (order_amount)

    last_price = get_last_price(client, ticker)
    error = True
    if upper_price > lower_price:
        if side == "b":
            if last_price > upper_price:
                error = False
            else:
                print("on buy side last price should be higher than upper price limit")
        elif side == "s":
            if last_price < lower_price:
                error = False
            else:
                print("on sell side last price should be lower than lower price limit")
        else:
            print(f"Error with side input || input: {side} || should be: b/s")
    else:
        print("upper price limit should be higher than lower price limit")

    if not error:
        if side == "b":
            usdt_balance = get_usdt_balance(client)
            side = "Buy"
            if usd_size < usdt_balance:
                single_order = int(usd_size / order_amount)
                price = lower_price
                for i in range(order_amount):
                    orders.append([round(single_order / price, decimals), round(price, tick_decimals)])
                    price += spacing

            else:
                print(f"Not enought usdt to execute the limit tranche order || usdt available: {usdt_balance} $")

        if side == "s":
            side = "Sell"
            coin_balance, usd_value = get_coin_balance(client, ticker)

            coins_to_sell = round(usd_size / ((upper_price + lower_price) / 2), decimals)
            single_order = round(coins_to_sell / order_amount, decimals)
            if coins_to_sell < coin_balance:
                price = lower_price
                for i in range(order_amount):
                    orders.append([single_order, round(price, tick_decimals)])
                    price += spacing
            else:
                print(f"not enough coins available to create limit tranche order || coin balance: {coin_balance}")

        for order in orders:
            client.place_order(category="spot", symbol=ticker, side=side, orderType="Limit", qty=order[0], price=order[1] ,timeInForce="GTC")
            time.sleep(0.01)

        print("orders created")


# market orders
def market_order(client, usd_size, ticker, side):
    """
    this order will split ur size into 20 equal orders and rapid execute them in 0.25s time intervals

    :param client: bybit client
    :param usd_size: size in usd
    :param ticker: choose ticker
    :param side:  b > buy, s > sell
    :return:
    """

    max_order_size_coin, min_order_size_coin, min_order_size_usd, max_order_size_usd, decimals, tick_size = get_instrument_info(client, ticker)

    orders = []
    if side == "b":
        usdt_balance = get_usdt_balance(client)
        side = "Buy"
        if usd_size < usdt_balance:
            single_order = int(usd_size / 20)
            if single_order > min_order_size_usd:
                if single_order < max_order_size_usd:
                    for i in range(20):
                        orders.append(single_order)
                else:
                    print(f"single order to big to execute twap || order size: {single_order} || max order size: {max_order_size_usd} ")
            else:
                print(f"total twap size to low: {usd_size}$")

    elif side == "s":
        # min order size is in coins
        coin_balance, usd_value = get_coin_balance(client, ticker)
        last_price = get_last_price(client, ticker)

        coins_to_sell = round(usd_size / last_price, decimals)
        side = "Sell"
        if usd_value > usd_size:
            single_order = round(coins_to_sell / 20, decimals)
            if single_order > min_order_size_coin:
                if single_order < max_order_size_coin:
                    for i in range(20):
                        orders.append(single_order)
                else:
                    print(f"single order to big to execute twap || order size: {single_order} coins|| max order size: {max_order_size_coin} coins ")
            else:
                print(f"total twap size to low: {usd_size}")
    else:
        print(f"Error with side input || input: {side} || should be: b/s")

    time_delay = 0.25   # seconds
    if orders:
        for order in orders:
            client.place_order(category="spot", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC")
            time.sleep(time_delay)


def linear_twap(client, usd_size, ticker, side, duration, order_amount):
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

    max_order_size_coin, min_order_size_coin, min_order_size_usd, max_order_size_usd, decimals, tick_size = get_instrument_info(client, ticker)

    # check if size doesn't excedes available usdt qty
    # if based on order amount size becomes lower than min qty fix it to min qty
    orders = []
    if side == "b":
        usdt_balance = get_usdt_balance(client)
        side = "Buy"
        if usd_size < usdt_balance:
            # min order size is in usd
            if order_amount == "default":
                single_order = int(usd_size / 100)
                if single_order > min_order_size_usd:
                    if single_order < max_order_size_usd:
                        for i in range(100):
                            orders.append(single_order)
                    else:
                        print(f"single order to big to execute twap || order size: {single_order} || max order size: {max_order_size_usd} ")
                else:
                    print(f"total twap size to low: {usd_size}")
            else:
                orders = []
                if int(usd_size / order_amount) > min_order_size_usd:
                    single_order = int(usd_size / order_amount)

                    if single_order < max_order_size_usd:
                        for i in range(order_amount):
                            orders.append(single_order)
                    else:
                        print(f"single order to big to execute twap || order size: {single_order} || max order size: {max_order_size_usd} ")
                else:
                    print(f"single order size to low to execute twap || order size: {int(usd_size / order_amount)} || min order size: {min_order_size_usd}")
        else:
            print(f"not enough usdt to execute twap || available funds: {usdt_balance} $ || twap size: {usd_size} $")

    elif side == "s":
        # min order size is in coins
        coin_balance, usd_value = get_coin_balance(client, ticker)
        last_price = get_last_price(client, ticker)

        coins_to_sell = round(usd_size / last_price, decimals)
        side = "Sell"
        if usd_value > usd_size:
            if order_amount == "auto":
                single_order = round(coins_to_sell / 100, decimals)
                if single_order > min_order_size_coin:
                    if single_order < max_order_size_coin:
                        for i in range(100):
                            orders.append(single_order)
                    else:
                        print(f"single order to big to execute twap || order size: {single_order} coins|| max order size: {max_order_size_coin} coins ")
                else:
                    print(f"total twap size to low: {usd_size} >> should be atleast 100$")
            else:
                orders = []
                single_order = round(coins_to_sell / order_amount, decimals)

                if single_order > min_order_size_coin:
                    if single_order < max_order_size_coin:
                        for i in range(order_amount):
                            orders.append(single_order)
                    else:
                        print(f"single order to big to execute twap || order size: {single_order} coins || max order size: {max_order_size_coin} coins")
                else:
                    print(f"single order size to low to execute twap || order size: {single_order} coins || min order size: {min_order_size_coin} coins")
        else:
            print(f"not enough usd value to execute twap || available funds: {usd_value} $ || twap size: {usd_size} $")

    else:
        print(f"Error with side input || input: {side} || should be: b/s")

    time_delay = duration / order_amount

    if orders:
        for order in orders:
            client.place_order(category="spot", symbol=ticker, side=side, orderType="Market", qty=order, timeInForce="IOC")
            time.sleep(time_delay)


# order execution functions

def set_limit_orders_usd(client):
    """
    Functions that sets basic limit orders

    :return:
    """
    tickers = get_spot_usdt_tickers(client=client)
    usd_size = cli_inputs.select_usdt_size()
    side = cli_inputs.select_side()
    ticker = cli_inputs.select_ticker(tickers=tickers)
    upper_price = cli_inputs.select_upper_limit_price()
    lower_price = cli_inputs.select_lower_limit_price()
    order_amount = cli_inputs.select_order_amount()

    limit_tranche(client=client, usd_size=usd_size, ticker=ticker, side=side, upper_price=upper_price, lower_price=lower_price, order_amount=order_amount)


def set_limit_orders_pct(client):
    """
       Functions that sets basic limit orders

       :return:
       """
    tickers = get_spot_usdt_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers)
    side = cli_inputs.select_side()
    upper_price = cli_inputs.select_upper_limit_price()
    lower_price = cli_inputs.select_lower_limit_price()
    avg_prc = (upper_price + lower_price) / 2
    if side == "s":
        coin_balance, usd_value = get_coin_balance(client=client, ticker=ticker)
        acc_pct = cli_inputs.select_pct()
        usd_size = round((coin_balance * avg_prc * 0.999) * acc_pct)
    else:
        usdt_balance = get_usdt_balance(client=client)
        acc_pct = cli_inputs.select_pct()
        usd_size = round(usdt_balance * acc_pct)

    order_amount = cli_inputs.select_order_amount()

    limit_tranche(client=client, usd_size=usd_size ,ticker=ticker, side=side, upper_price=upper_price, lower_price=lower_price, order_amount=order_amount)


def set_linear_twap_usd(client):
    """
    Basic linear twap setup

    :param client:
    :return:
    """
    tickers = get_spot_usdt_tickers(client=client)
    usd_size = cli_inputs.select_usdt_size()
    side = cli_inputs.select_side()
    ticker = cli_inputs.select_ticker(tickers=tickers)
    duration = cli_inputs.select_duration()
    order_amount = cli_inputs.select_order_amount()

    twap_thread = Thread(target=linear_twap, args=(client, usd_size, ticker, side, duration, order_amount), name=f"BYBIT_SPOT_{ticker}_{side}_{usd_size}_twap{round(duration / 60, 1)}min").start()


def set_linear_twap_pct(client):
    """
    Basic linear twap setup

    :param client:
    :return:
    """
    tickers = get_spot_usdt_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers)
    side = cli_inputs.select_side()

    if side == "s":
        coin_balance, usd_value = get_coin_balance(client=client, ticker=ticker)
        acc_pct = cli_inputs.select_pct()
        usd_size = round(usd_value * acc_pct)
    else:
        usdt_balance = get_usdt_balance(client=client)
        acc_pct = cli_inputs.select_pct()
        usd_size = round(usdt_balance * acc_pct)

    duration = cli_inputs.select_duration()
    order_amount = cli_inputs.select_order_amount()

    twap_thread = Thread(target=linear_twap, args=(client, usd_size, ticker, side, duration, order_amount), name=f"BYBIT_SPOT_{ticker}_{side}_{usd_size}_twap{round(duration / 60, 1)}min").start()


def set_market_order_usd(client):
    """
    Basic market order executes in 20 swarm orders

    :param client:
    :return:
    """

    tickers = get_spot_usdt_tickers(client=client)
    usd_size = cli_inputs.select_usdt_size()
    side = cli_inputs.select_side()
    ticker = cli_inputs.select_ticker(tickers=tickers)

    market_order_thread = Thread(target=market_order, args=(client, usd_size, ticker, side), name=f"SPOT_{ticker}_{side}_{usd_size}").start()


def set_market_order_pct(client):
    """
    Basic market order executes in 20 swarm orders

    :param client:
    :return:
    """
    usdt_balance = get_usdt_balance(client=client)

    tickers = get_spot_usdt_tickers(client=client)
    ticker = cli_inputs.select_ticker(tickers=tickers)
    side = cli_inputs.select_side()

    if side == "s":
        coin_balance, usd_value = get_coin_balance(client=client, ticker=ticker)
        acc_pct = cli_inputs.select_pct()
        usd_size = round(usd_value * acc_pct)
    else:
        usdt_balance = get_usdt_balance(client=client)
        acc_pct = cli_inputs.select_pct()
        usd_size = round(usdt_balance * acc_pct)

    market_order_thread = Thread(target=market_order, args=(client, usd_size, ticker, side), name=f"SPOT_{ticker}_{side}_{usd_size}").start()

# todo: TESTING
# api_key, api_secret = get_credentials(account="personal")
# client = auth(api_key, api_secret)
#
# get_all_spot_positions(client)

# set_limit_orders_usd(client)
# set_limit_orders_pct(client)

# set_limit_orders_atAvgPrc_usd(client)
# set_limit_orders_atAvgPrc_pct(client)

# set_linear_twap_usd(client)
# set_market_order_usd(client)

# set_linear_twap_pct(client)
# set_market_order_pct(client)

# todo: dodat price checke da štima glede uper limit itd da so zadeve logične uglavnem pa da nemorš ful velke cifre dat

# limit_tranche(client, 500, "ETHUSDT", "s", 1850, 1810, 10)

# limit_tranche_avg_price(client, 1000, "ETHUSDT", "s",1850, 1810, 1833 ,10)


# linear_twap(client, 1965, "ETHUSDT", "s", 30, 10)
# market_order(client, 1000, "ETHUSDT", "s")


# tickers = get_spot_usdt_tickers(client)
# max_order_size_coin, min_order_size_coin, min_order_amount, max_order_amount, decimals = get_instrument_info(client, "BTCUSDT")
# balance = get_usdt_balance(client)
