import pandas as pd
import numpy as np
import features
import matplotlib.pyplot as plt


def add_features(df):
    # Create features
    # df["o_scaled_50"] = df["o"].rolling(window=50, min_periods=50, axis=0).apply(lambda x: (x[-1] - np.min(x)) / (np.max(x) - np.min(x)), raw=True)
    df["rsi_s"] = features.get_rsi(df, period=30)
    df["rsi_f"] = features.get_rsi(df, period=5)
    df["stoch_rsi"] = features.get_stoch_rsi(df["c"], period=14)
    df["stoch"] = features.get_stoch(df, period=14)

    # We don't have to perform shifting, because we use the open price
    df["std_short"] = df["o"].rolling(20).std()
    df["std_long"] = df["o"].rolling(200).std()
    df["std_factor"] = df["std_short"]/df["std_long"]

    # Drop nans at beginning and end
    first_ix = df.first_valid_index()
    last_ix = df.last_valid_index()
    df = df.loc[first_ix:last_ix]

    return df


def add_entry_signal(row):
    rsi_threshold = 40
    stoch_rsi_threshold = 25
    stoch_threshold = 35

    # If oversold:
    if (row["rsi_f"] < rsi_threshold) and (row["rsi_s"] < rsi_threshold)and (row["stoch_rsi"] < stoch_rsi_threshold) and (row["stoch"] < stoch_threshold):
        return 1
    # Else
    else:
        return 0


def check_exit(row, open_price, take_profit_pct, stop_loss_pct, spread_pct):
    return_high = (row["h"] / open_price) - 1
    return_low = (row["l"] / open_price) - 1
    # print(row, return_low, return_high)

    temp_profit = 0
    close_price = None
    if return_high >= take_profit_pct:
        temp_profit = open_price * (take_profit_pct - 2*spread_pct)
        close_price = round(open_price*(1+take_profit_pct), 4)
    elif return_low <= -stop_loss_pct:
        temp_profit = -open_price * (stop_loss_pct + 2*spread_pct)
        close_price = round(open_price*(1-stop_loss_pct), 4)
    return temp_profit, close_price


def perform_backtest(df, market):
    """
    Note; Inaccuracy due to
    :param df:
    :return:
    """
    take_profit_pct = 3/100
    stop_loss_pct = 4/100
    position = 0
    profit = 0
    spread_pct = 0.075/100
    profit_list = [0]
    trade_dates = [df.loc[0]["d"]]
    for ix in df.index:
        if position == 0:
            if df.loc[ix]["entry"] == 1:
                position = 1
                open_price = df.loc[ix]["o"]
                print(f"Open long: {df.loc[ix]['d']} at {open_price}")

                # Check if we can close already (we open at opening bar,so we have a h/l to process)
                profit_update, close_price = check_exit(df.loc[ix], open_price, take_profit_pct, stop_loss_pct, spread_pct)
                if profit_update != 0:
                    profit += profit_update
                    trade_dates += [df.loc[ix]["d"]]
                    profit_list += [profit]
                    position = 0
                    print(f"Close long: {df.loc[ix]['d']} {close_price}. Trade profit: {profit_update}. Total profit: {profit}\n")
        # If we are long
        elif position > 0:
            # Check if we can close already (we open at opening bar,so we have a h/l to process)
            profit_update, close_price = check_exit(df.loc[ix], open_price, take_profit_pct, stop_loss_pct, spread_pct)
            if profit_update != 0:
                profit += profit_update
                position = 0
                trade_dates += [df.loc[ix]["d"]]
                profit_list += [profit]
                print(f"Close long: {df.loc[ix]['d']} {close_price}. Trade profit: {profit_update}. Total profit: {profit}\n")
        # Short not implemented
        elif position < 0:
            print("Not implemented")

    plt.plot(trade_dates, profit_list)
    plt.grid()
    plt.savefig(f"{market}.png")
    plt.xticks(rotation=90)


markets = ["BTCUSDT"]

for market in markets:
    # Read data and add features
    df = pd.read_csv(f"{market}.csv")
    df = df.sort_values("d")
    df = add_features(df)
    df["d"] = pd.to_datetime(df["d"])
    df["entry"] = df.apply(add_entry_signal, axis=1).shift(1)

    # Create train test_split
    cutoff_date = pd.to_datetime("2010-01-01 00:00:00")
    max_date = pd.to_datetime("2021-01-01 00:00:00")
    # df_train = df[df["d"] <= cutoff_date].reset_index(drop=True)
    df_val = df[(df["d"] > cutoff_date) & (df["d"] < max_date)].reset_index(drop=True)

    # Perform backtest
    perform_backtest(df_val, market)
