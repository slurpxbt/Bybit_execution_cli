# CLI inputs
def select_ticker(tickers):
    ticker_selected = False
    while not ticker_selected:
        try:
            input_ticker = input("select ticker[without denominator -> ex: btc] >>> ")
            ticker = tickers[input_ticker.upper()]
            print(f"{ticker} selected")
            ticker_selected = True
            return ticker
        except:
            print("Invalid ticker selected >> try again")


def select_order_amount():
    """
    :return: number of orders
    """
    order_amount_selected = False
    while not order_amount_selected:
        order_number = input("select number of orders or type def for default option[15 orders] >>> ")
        try:
            if order_number.lower() == "def":
                order_number = "default"
                order_amount_selected = True
                return order_number
            else:
                order_number = int(order_number)
                order_amount_selected = True
                return order_number
        except:
            print("Error selecting number of orders: input must be number")


def select_usdt_size():
    """
    :return: position size in usdt
    """
    size_selected = False
    while not size_selected:
        input_size = input("select position size[usdt] >>> ")
        try:
            input_size = int(input_size)
            size_selected = True
            return input_size
        except:
            print("Error selecting positions size: input must be number")


def select_duration():
    """
    :return: duration in seconds
    """
    duration_selected = False
    while not duration_selected:

        input_duration = input("select duration minutes >>> ")
        try:
            input_duration = float(input_duration) * 60
            duration_selected = True
            return input_duration
        except:
            print("Error selecting duration input must be number")


def select_side():
    """
    :return: order side
    """
    side_selected = False
    while not side_selected:
        input_side = input("select side b=Buy, s=Sell >>> ")
        if input_side.lower() == "b":
            input_side = input_side.lower()
            side_selected = True
            return input_side
        elif input_side.lower() == "s":
            input_side = input_side.lower()
            side_selected = True
            return input_side
        else:
            print("Error with selecting side")


def select_pct():
    """
    :return: % in basis points from 0-1
    """
    pct_selected = False
    while not pct_selected:

        pct_input = input("select how much of acc. you want to buy/sell [1-100 %] >>> ")
        try:
            if 0 < float(pct_input) <= 100:
                pct_input = float(pct_input) / 100
                if pct_input == 100:
                    pct_input = 99.9

                pct_selected = True
                return pct_input
            else:
                print("Error choose % between 1 and 100")
        except:
            print("Error selecting %: input must be number")


def select_upper_limit_price():
    """

    :return: upper limit price for limit order tranche
    """
    price_selected = False
    while not price_selected:

        input_price = input("input upper limit price >>> ")
        try:
            input_price = float(input_price)
            price_selected = True
            return input_price
        except:
            print("Error selecting upper limit price")


def select_lower_limit_price():
    """
    :return: lower limit price for limit order tranche
    """
    price_selected = False
    while not price_selected:
        input_price = input("input lower limit price >>> ")
        try:
            input_price = float(input_price)
            price_selected = True
            return input_price
        except:
            print("Error selecting lower limit price")


def select_avg_limit_price():
    """
    :return: avg limit price for limit order tranche
    """
    price_selected = False
    while not price_selected:
        input_price = input("input avg limit price >>> ")
        try:
            input_price = float(input_price)
            price_selected = True
            return input_price
        except:
            print("Error selecting avg limit price")


def select_lookback_window():
    """
    :return: lookcback window[hours]
    """
    window_selected = False
    while not window_selected:
        input_number = input("select lookback window[hours] >>> ")
        try:
            input_number = int(input_number)
            window_selected = True
            return input_number
        except:
            print("Error selecting lookback window")


def select_upper_pct():
    """
    :return: % in basis points from 0-1
    """
    pct_selected = False
    while not pct_selected:

        pct_input = input("select upper % point of where you want to bid >>> ")
        try:
            if 0 < float(pct_input) <= 100:
                pct_input = float(pct_input) / 100
                if pct_input == 100:
                    pct_input = 99.9

                pct_selected = True
                return pct_input
            else:
                print("Error choose % between 1 and 100")
        except:
            print("Error selecting %: input must be number")


def select_lower_pct():
    """
    :return: % in basis points from 0-1
    """
    pct_selected = False
    while not pct_selected:

        pct_input = input("select lower % point of where you want to bid >>> ")
        try:
            if 0 < float(pct_input) <= 100:
                pct_input = float(pct_input) / 100
                if pct_input == 100:
                    pct_input = 99.9

                pct_selected = True
                return pct_input
            else:
                print("Error choose % between 1 and 100")
        except:
            print("Error selecting %: input must be number")