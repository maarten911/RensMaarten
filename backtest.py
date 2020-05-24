import pandas as pd
import numpy as np
import features


def add_features(df):
    # Create features
    # df["std_10"] = df["o"].rolling(10).std()
    # df["std_20"] = df["o"].rolling(20).std()
    df["o_scaled_50"] = df["o"].rolling(window=50, min_periods=50, axis=0).apply(lambda x: (x[-1] - np.min(x)) / (np.max(x) - np.min(x)), raw=True)
    df["o_scaled_250"] = df["o"].rolling(window=250, min_periods=250, axis=0).apply(lambda x: (x[-1] - np.min(x)) / (np.max(x) - np.min(x)), raw=True)
    df["rsi"] = features.get_rsi(df, window=15)

    return df
