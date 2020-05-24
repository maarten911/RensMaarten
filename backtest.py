import pandas as pd
import numpy as np
import features


def add_features(df):
    # Create features
    df["o_scaled_50"] = df["o"].rolling(window=50, min_periods=50, axis=0).apply(lambda x: (x[-1] - np.min(x)) / (np.max(x) - np.min(x)), raw=True)
    df["rsi"] = features.get_rsi(df, period=15)
    df["stoch_rsi"] = features.get_stoch_rsi(df["c"], period=14, smoothD=3, smoothK=3)

    # Drop nans at beginning and end
    first_ix = df.first_valid_index()
    last_ix = df.last_valid_index()
    df = df.loc[first_ix:last_ix]

    return df


def add_entry_signal(row):
    rsi_threshold = 20

    # If oversold:
    if row["rsi"] < rsi_threshold:
        return -1
    # If overbought
    elif row["rsi"] > 100 - rsi_threshold:
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


def perform_backtest(df):
    """
    Note; Inaccuracy due to
    :param df:
    :return:
    """
    take_profit_pct = 3/100
    stop_loss_pct = 4/100
    position = 0
    profit = 0
    spread_pct = 0.75/100

    for ix in df.index:
        if position == 0:
            if df.loc[ix]["entry"] == 1:
                position = 1
                open_price = df.loc[ix]["o"]
                print(f"Open long: {df.loc[ix]['d']} at open_price")

                # Check if we can close already (we open at opening bar,so we have a h/l to process)
                profit_update, close_price = check_exit(df.loc[ix], open_price, take_profit_pct, stop_loss_pct, spread_pct)
                if profit_update != 0:
                    profit += profit_update
                    position = 0
                    print(f"Close long: {df.loc[ix]['d']} {close_price}. Trade profit: {profit_update}. Total profit: {profit}\n")
        # If we are long
        elif position > 0:
            # Check if we can close already (we open at opening bar,so we have a h/l to process)
            profit_update, close_price = check_exit(df.loc[ix], open_price, take_profit_pct, stop_loss_pct, spread_pct)
            if profit_update != 0:
                profit += profit_update
                position = 0
                print(f"Close long at {close_price}. Trade profit: {profit_update}. Total profit: {profit}\n")
        # Short not implemented
        elif position < 0:
            print("Not implemented")


# Read data and add features
df = pd.read_csv("BTCUSDT.csv")
df = df.sort_values("d")
df = add_features(df)
df["d"] = pd.to_datetime(df["d"])
df["entry"] = df.apply(add_entry_signal, axis=1).shift(1)

# Create train test_split
cutoff_date = pd.to_datetime("2019-07-01 00:00:00")
max_date = pd.to_datetime("2020-01-01 00:00:00")
df_train = df[df["d"] <= cutoff_date].reset_index(drop=True)
df_val = df[(df["d"] > cutoff_date) & (df["d"] < max_date)].reset_index(drop=True)

# Perform backtest
perform_backtest(df_train)
print(df_train)
print(df_val)
