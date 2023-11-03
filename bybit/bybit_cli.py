import bybit_spot
import bybit_usdt_futures
import threading


def get_all_running_threads():
    if len(threading.enumerate()) == 1:
        print("No running proceses")
    else:
        print("Current running processes:")
        for thread in threading.enumerate():
            if thread.name != "MainThread":
                print(thread.name)


def bybit_spot_cli(account):

    api_key, api_secret = bybit_spot.get_credentials(account=account)
    client = bybit_spot.auth(api_key, api_secret)

    exit = False
    while not exit:
        print("What do you want to do:"
              "\n 1 >> display positions"
              "\n 2 >> market orders"
              "\n 3 >> limit orders"
              "\n 4 >> TWAPS"
              "\n 0 >> exit - bybit SPOT"
              "\n 99 >> restart client"
              "\n 999 >> check current running processes")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print(f"Bybit SPOT >> {account} account - closing")
        elif mode == 1:
            bybit_spot.get_all_spot_positions(client)
        elif mode == 2:
            print("\n")
            print("Market order mode selected >> options:"
                  "\n 1 >> market order by $ amount"
                  "\n 2 >> market order by acc %")
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                bybit_spot.set_market_order_usd(client)
            elif order_mode == 2:
                bybit_spot.set_market_order_pct(client)

            print("\n")
        elif mode == 3:
            print("\n")
            print("Limit order mode selected >> options:"
                  "\n 1 >> limit orders between 2 prices by $ amount"
                  "\n 2 >> limit orders between 2 prices by account %"
                  "\n 3 >> limit orders between 2 prices by $ amount at specific avg. price"
                  "\n 4 >> limit orders between 2 prices by account % at specific avg. price"
                  )
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                bybit_spot.set_limit_orders_usd(client)
            elif order_mode == 2:
                bybit_spot.set_limit_orders_pct(client)
            elif order_mode == 3:
                bybit_spot.set_limit_orders_atAvgPrc_usd(client)
            elif order_mode == 4:
                bybit_spot.set_limit_orders_atAvgPrc_pct(client)

            print("\n")
        elif mode == 4:
            print("TWAP mode selected >> options:"
                  "\n 1 >> linear twap by $ amount"
                  "\n 2 >> linear twap by account %")
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                bybit_spot.set_linear_twap_usd(client)
            elif order_mode == 2:
                bybit_spot.set_linear_twap_pct(client)
        elif mode == 999:
            print("\n")
            get_all_running_threads()
            print("\n")
        elif mode == 99:
            print("Reconnecting client")
            api_key, api_secret = bybit_spot.get_credentials(account=account)
            client = bybit_spot.auth(api_key, api_secret)
            print("\n")


def bybit_futures_cli(account):
    api_key, api_secret = bybit_spot.get_credentials(account=account)
    client = bybit_spot.auth(api_key, api_secret)

    exit = False
    while not exit:
        print("What do you want to do:"
              "\n 1 >> display positions"
              "\n 2 >> open position"
              "\n 3 >> close/reduce position"
              "\n 4 >> modify tp/sl"
              "\n 0 >> exit - bybit Futures"
              "\n 99 >> restart client"
              "\n 999 >> check current running processes")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print(f"Bybit Futures >> {account} account - closing")
        elif mode == 1:
            print("\n")
            bybit_usdt_futures.get_open_positions(client, display=True)
            print("\n")
        elif mode == 2:
            print("Open position mode selected >> options:"
                  "\n 1 >> market orders"
                  "\n 2 >> limit orders"
                  "\n 3 >> TWAPS")
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                bybit_usdt_futures.set_market_order_open(client)
            elif order_mode == 2:
                print("\n")
                print("Limit order mode seleceted >> options:"
                      "\n 1 >> limit orders between 2 prices by $ amount"
                      "\n 2 >> limit orders between 2 prices by $ amount at specific avg. price"
                      )
                limit_order_mode = int(input("input number >>> "))
                if limit_order_mode == 1:
                    bybit_usdt_futures.set_limits_open(client)
                elif limit_order_mode == 2:
                    bybit_usdt_futures.set_limits_at_avgPrc_open(client)
            elif order_mode == 3:
                bybit_usdt_futures.set_linear_twap_open(client)
        elif mode == 3:
            print("Close / reduce position mode selected >> options:"
                  "\n 1 >> market orders"
                  "\n 2 >> limit orders"
                  "\n 3 >> TWAPS")
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                bybit_usdt_futures.set_market_order_close(client)
            elif order_mode == 2:
                print("\n")
                print("Limit order mode seleceted >> options:"
                      "\n 1 >> limit orders between 2 prices by $ amount"
                      "\n 2 >> limit orders between 2 prices by $ amount at specific avg. price"
                      )
                limit_order_mode = int(input("input number >>> "))
                if limit_order_mode == 1:
                    bybit_usdt_futures.set_limits_close(client)
                elif limit_order_mode == 2:
                    bybit_usdt_futures.set_limits_at_avgPrc_close(client)
            elif order_mode == 3:
                bybit_usdt_futures.set_linear_twap_close(client)
        elif mode == 4:
            bybit_usdt_futures.set_position_sl_tp(client)
        elif mode == 999:
            print("\n")
            get_all_running_threads()
            print("\n")
        elif mode == 99:
            print("Reconnecting client")
            api_key, api_secret = bybit_usdt_futures.get_credentials(account=account)
            client = bybit_usdt_futures.auth(api_key, api_secret)
            print("\n")


def main():

    exit = False
    while not exit:
        print("\n")
        print("Select account:"
              "\n 1 >> Bybit SPOT personal"
              "\n 2 >> Bybit USDT perps - personal"
              "\n 999 >> check current running processes"
              "\n 0 >> exit terminal")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print("\n")
            print("Terminal closing")
        elif mode == 999:
            print("\n")
            get_all_running_threads()
            print("\n")
        elif mode == 1:
            print("\n")
            bybit_spot_cli(account="personal")
        elif mode == 2:
            print("\n")
            bybit_futures_cli(account="personal")

if __name__ == "__main__":
    main()