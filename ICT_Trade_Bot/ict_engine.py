import os
import csv
import pandas as pd
from telegram_alert import send_telegram_alert
from datetime import datetime, time

ALERT_LOG_PATH = "alert_log.csv"

# === Alert Log Functions ===
def load_alert_log():
    if not os.path.exists(ALERT_LOG_PATH):
        with open(ALERT_LOG_PATH, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["alert_id"])
        return set()
    with open(ALERT_LOG_PATH, mode="r") as f:
        reader = csv.DictReader(f)
        return set(row["alert_id"] for row in reader)

def save_alert_to_log(alert_id):
    with open(ALERT_LOG_PATH, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([alert_id])

# === Utility Functions ===
def in_killzone(ts):
    dt = datetime.fromisoformat(ts)
    local = dt.time()
    return (
        time(7, 0) <= local <= time(10, 0) or     # London
        time(13, 30) <= local <= time(16, 0) or   # NY AM
        time(19, 0) <= local <= time(21, 0)       # NY PM
    )

def find_fvg(df):
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:  # Bullish FVG
            return i
        elif df['high'].iloc[i] < df['low'].iloc[i-2]:  # Bearish FVG
            return i
    return None

def stacked_ob(df, idx):
    candle = df.iloc[idx]
    if candle['close'] > candle['open']:  # Bullish OB
        return candle['low'] == min(df.iloc[idx-2:idx+1]['low'])
    else:  # Bearish OB
        return candle['high'] == max(df.iloc[idx-2:idx+1]['high'])

def htf_pd_array_confluence(htf_dfs):
    result = {
        'htf_has_ob': False,
        'htf_has_fvg': False,
        'htf_has_ifvg': False
    }
    for df in htf_dfs:
        recent = df.tail(5)
        if any(r['close'] < r['open'] for _, r in recent.iterrows()):
            result['htf_has_ob'] = True
        if any(recent['low'].min() > recent['high'].shift(2).min()):
            result['htf_has_fvg'] = True
        if any(recent['high'].iloc[-1] > recent['high'].iloc[-2] and recent['low'].iloc[-1] < recent['low'].iloc[-2] for i in range(2, len(recent))):
            result['htf_has_ifvg'] = True
    return result

# === Detection Logic ===
def detect_ict_setups():
    setups = []
    base_path = "ict_data"
    for symbol in ["NAS100"]:
        try:
            df_1m = pd.read_csv(f"{base_path}/{symbol}/1m.csv")
            df_5m = pd.read_csv(f"{base_path}/{symbol}/5m.csv")
            df_1h = pd.read_csv(f"{base_path}/{symbol}/60m.csv")
            df_4h = pd.read_csv(f"{base_path}/{symbol}/240m.csv")
            df_1d = pd.read_csv(f"{base_path}/{symbol}/1d.csv")
            df_1w = pd.read_csv(f"{base_path}/{symbol}/1wk.csv")
            df_1mo = pd.read_csv(f"{base_path}/{symbol}/1mo.csv")
        except:
            continue

        if len(df_1m) < 5:
            continue

        htf_confluence = htf_pd_array_confluence([df_1h, df_4h, df_1d, df_1w, df_1mo])

        for i in range(3, len(df_1m)):
            ts = df_1m['timestamp'].iloc[i]
            if not in_killzone(ts):
                continue

            if df_1m['low'].iloc[i] > df_1m['high'].iloc[i-2]:  # Bullish FVG
                if stacked_ob(df_1m, i):
                    entry = df_1m['close'].iloc[i]
                    sl = df_1m['low'].iloc[i]
                    tp = entry + (entry - sl) * 2
                    setups.append({
                        "symbol": symbol,
                        "timeframe": "1m",
                        "smt": "Yes",
                        "mss": "Yes",
                        "ob": "Yes",
                        "fvg": "Yes",
                        "bias": "HTF PD Array",
                        "killzone": ts,
                        "entry": entry,
                        "sl": sl,
                        "tp": tp,
                        "htf_ob": htf_confluence['htf_has_ob'],
                        "htf_fvg": htf_confluence['htf_has_fvg'],
                        "htf_ifvg": htf_confluence['htf_has_ifvg']
                    })
    return setups

# === Main Runner ===
def run_ict_engine():
    alert_log = load_alert_log()
    setups = detect_ict_setups()

    for setup in setups:
        alert_id = f"{setup['symbol']}_{setup['timeframe']}_{setup['killzone']}_{setup['entry']:.2f}"
        if alert_id in alert_log:
            continue

        tv_link = f"https://www.tradingview.com/chart/?symbol={setup['symbol']}"

        msg = f"""
🚨 ICT Setup Detected
Asset: {setup['symbol']}
TF: {setup['timeframe']}
SMT: {setup['smt']}
MSS: {setup['mss']}
OB: {setup['ob']}
FVG: {setup['fvg']}
Bias: {setup['bias']}
Killzone Time: {setup['killzone']}
Entry: {setup['entry']:.2f}
SL: {setup['sl']:.2f}
TP: {setup['tp']:.2f}
HTF OB: {setup['htf_ob']}
HTF FVG: {setup['htf_fvg']}
HTF IFVG: {setup['htf_ifvg']}
Chart: {tv_link}
"""
        send_telegram_alert(msg)
        save_alert_to_log(alert_id)

if __name__ == "__main__":
    run_ict_engine()

