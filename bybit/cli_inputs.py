# CLI inputs
def select_ticker(tickers):
    try:
        input_ticker = input("select ticker[without denominator -> ex: btc] >>> ")
        ticker = tickers[input_ticker.upper()]
        print(f"{ticker} selected")
        return ticker
    except:
        print("Invalid ticker selected")
        return None


def select_order_amount():
    """

    :return: number of orders
    """
    order_number = input("select number of orders or type def for default option[15 orders] >>> ")
    try:
        if order_number.lower() == "def":
            order_number = "default"
            return order_number
        else:
            order_number = int(order_number)
            return order_number
    except:
        print("Error selecting number of orders: input must be number")
        return None


def select_usdt_size():
    """

    :return: position size in usdt
    """
    input_size = input("select position size[usdt] >>> ")
    try:
        input_size = int(input_size)
        return input_size
    except:
        print("Error selecting positions size: input must be number")
        return None


def select_duration():
    """

    :return: duration in seconds
    """
    input_duration = input("select duration minutes >>> ")
    try:
        input_duration = float(input_duration) * 60
        return input_duration
    except:
        print("Error selecting duration input must be number")
        return None


def select_side():
    """

    :return: order side
    """
    input_side = input("select side b=Buy, s=Sell >>> ")
    if input_side.lower() == "b":
        input_side = input_side.lower()
        return input_side
    elif input_side.lower() == "s":
        input_side = input_side.lower()
        return input_side
    else:
        print("Error with selecting side")
        return None




def select_pct():
    """

    :return: % in basis points from 0-1
    """
    pct_input = input("select how much of acc. you want to buy/sell [1-100 %] >>> ")
    try:
        if 0 < int(pct_input) <= 100:
            pct_input = int(pct_input) / 100
            return pct_input
        else:
            print("Error choose % between 1 and 100")
    except:
        print("Error selecting positions size: input must be number")
        return None


def select_upper_limit_price():
    """

    :return: upper limit price for limit order tranche
    """
    input_price = input("input upper limit price >>> ")
    try:
        input_price = float(input_price)
        return input_price
    except:
        print("Error selecting upper limit price")
        return None


def select_lower_limit_price():
    """

    :return: lower limit price for limit order tranche
    """
    input_price = input("input lower limit price >>> ")
    try:
        input_price = float(input_price)
        return input_price
    except:
        print("Error selecting lower limit price")
        return None


def select_avg_limit_price():
    """

    :return: avg limit price for limit order tranche
    """
    input_price = input("input avg limit price >>> ")
    try:
        input_price = float(input_price)
        return input_price
    except:
        print("Error selecting avg limit price")
        return None


def select_lookback_window():
    """
    :return: lookcback window[hours]
    """
    input_price = input("select lookback window[hours] >>> ")
    try:
        input_price = int(input_price)
        return input_price
    except:
        print("Error selecting lookback window")
        return None
