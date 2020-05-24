import pandas as pd
import matplotlib.pyplot as plt

market ="BTCUSDT"
df = pd.read_csv(f"{market}.csv")
df["d"] = pd.to_datetime(df["d"])
df = df[df["d"] > pd.to_datetime("2020-01-01 00:00:00")]
df = df.iloc[::50, :]
df = df.sort_values("d")
plt.plot(df["d"], df["c"])
plt.grid()
plt.savefig(f"{market}-data.png")
