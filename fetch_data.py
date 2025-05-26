import yfinance as yf
import pandas as pd
import os

symbols = ["^NDX", "^GSPC", "EURUSD=X", "GBPUSD=X", "DX-Y.NYB"]
names = ["NAS100", "SP500", "EURUSD", "GBPUSD", "DXY"]
intervals = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "60m",
    "4h": "240m",
    "1d": "1d",
    "1wk": "1wk",
    "1mo": "1mo"
}

for sym, name in zip(symbols, names):
    for tf, intv in intervals.items():
        print(f"Fetching {name} [{tf}]...")
        try:
            df = yf.download(sym, interval=intv, period="60d" if tf in ["1m", "5m", "15m"] else "6mo")
            df = df.reset_index()
            df = df.rename(columns={"Datetime": "timestamp", "Date": "timestamp"})
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            os.makedirs(f"ict_data/{name}", exist_ok=True)
            df.to_csv(f"ict_data/{name}/{tf}.csv", index=False)
        except Exception as e:
            print(f"❌ Failed to fetch {name} {tf}: {e}")
print("✅ All data fetched.")
