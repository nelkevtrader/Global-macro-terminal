import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import hashlib

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal — Deterministic Snapshot Engine")

API = "https://global-macro-terminal-1.onrender.com/global-state"

# =========================================================
# SNAPSHOT CACHE (CORE FIX)
# =========================================================
SNAPSHOT_TTL = 300  # 5 minutes fixed snapshot window

if "snapshot" not in st.session_state:
    st.session_state.snapshot = None

if "snapshot_time" not in st.session_state:
    st.session_state.snapshot_time = 0

# =========================================================
# SAFE REQUEST
# =========================================================
def safe_get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=6)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# =========================================================
# SNAPSHOT ENGINE
# =========================================================
def should_refresh():
    return time.time() - st.session_state.snapshot_time > SNAPSHOT_TTL

def build_snapshot():
    data = safe_get(API) or {"countries": {}, "regime": "Unknown"}

    return {
        "data": data,
        "timestamp": time.time()
    }

if st.session_state.snapshot is None or should_refresh():
    st.session_state.snapshot = build_snapshot()
    st.session_state.snapshot_time = time.time()

snapshot = st.session_state.snapshot
data = snapshot["data"]

# =========================================================
# RECONCILIATION ENGINE
# =========================================================
def reconcile(values):
    vals = [v for v in values if isinstance(v, (int, float))]
    if len(vals) == 0:
        return None, None, "NO DATA"

    median = float(np.median(vals))
    spread = float(np.std(vals)) if len(vals) > 1 else 0.0

    if spread < 0.01:
        conf = "HIGH"
    elif spread < 0.05:
        conf = "MEDIUM"
    else:
        conf = "LOW"

    return median, spread, conf

# =========================================================
# FX ENGINE (STABLE PER SNAPSHOT)
# =========================================================
fx_raw = safe_get("https://open.er-api.com/v6/latest/USD")
fx = fx_raw["rates"] if fx_raw else {}

def fx_move(currency):
    v = fx.get(currency)
    if not v:
        return 0.0
    return min(abs(np.log(v)) * 10, 100)

# =========================================================
# BTC (STABLE PER REFRESH CYCLE)
# =========================================================
def get_btc():
    v1 = None
    v2 = None

    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids": "bitcoin", "vs_currencies": "usd"},
                         timeout=6)
        v1 = r.json()["bitcoin"]["usd"]
    except:
        pass

    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
                         timeout=6)
        v2 = float(r.json()["price"])
    except:
        pass

    return reconcile([v1, v2])

btc_price, btc_spread, btc_conf = get_btc()

# =========================================================
# GOLD (FULLY STABLE + SAFE)
# =========================================================
def get_gold():
    v1 = None
    v2 = None

    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote",
            params={"symbols": "GC=F"},
            timeout=6
        )
        res = r.json()["quoteResponse"]["result"]
        if res:
            v1 = res[0].get("regularMarketPrice")
    except:
        pass

    try:
        r = requests.get("https://stooq.com/q/l/?s=xauusd&i=d", timeout=6)
        line = r.text.split("\n")[1].split(",")
        v2 = float(line[3])
    except:
        pass

    return reconcile([v1, v2])

gold_price, gold_spread, gold_conf = get_gold()

# =========================================================
# DATAFRAME (FROM SNAPSHOT ONLY)
# =========================================================
df = pd.DataFrame(list(data["countries"].items()), columns=["Currency", "Stress"])

currency_map = {
    "EGP": "Egypt","TRY": "Turkey","ARS": "Argentina",
    "NGN": "Nigeria","ZAR": "South Africa","PKR": "Pakistan",
    "LKR": "Sri Lanka","GHS": "Ghana","KES": "Kenya",
    "USD": "United States","EUR": "Eurozone","JPY": "Japan",
    "GBP": "United Kingdom","CNY": "China","INR": "India",
    "BRL": "Brazil","MXN": "Mexico","RUB": "Russia",
    "IDR": "Indonesia","VND": "Vietnam"
}

df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df["Stress (%)"] = (df["Stress"] * 100).round(2)

# IMPORTANT: deterministic (NO DRIFT)
df["Delta (%)"] = df["Stress"].diff().fillna(0).values * 100

df["FX Move (%)"] = df["Currency"].apply(fx_move)

df["Signal (%)"] = (
    df["Stress (%)"] * 0.65 +
    df["Delta (%)"].abs() * 0.2 +
    df["FX Move (%)"] * 0.15
)

df["Signal (%)"] = df["Signal (%)"].clip(0, 100).round(2)

def risk(x):
    if x > 75:
        return "🔴 High Risk"
    elif x > 60:
        return "🟠 Warning"
    elif x > 40:
        return "🟡 Elevated"
    return "🟢 Stable"

df["Risk"] = df["Signal (%)"].apply(risk)

# =========================================================
# HEADER
# =========================================================
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Bitcoin", f"${btc_price:,.0f}" if btc_price else "N/A")

with c2:
    st.metric("Gold", f"${gold_price:,.0f}" if gold_price else "N/A")

with c3:
    st.metric("Regime", data["regime"])

st.caption(f"Snapshot locked at: {time.ctime(snapshot['timestamp'])}")

st.divider()

# =========================================================
# DATA QUALITY
# =========================================================
st.subheader("🧠 Data Reconciliation Layer")

st.write(f"BTC: {btc_price} | {btc_conf}")
st.write(f"Gold: {gold_price} | {gold_conf}")

st.divider()

# =========================================================
# TABLES
# =========================================================
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False)
    [["Label","Stress (%)","Signal (%)","Risk"]]
    .head(5),
    use_container_width=True
)

st.subheader("🌍 Full Macro Snapshot")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)","FX Move (%)","Signal (%)","Risk"]],
    use_container_width=True
)

# =========================================================
# REFRESH CONTROL
# =========================================================
if st.button("Force Refresh Snapshot"):
    st.session_state.snapshot = build_snapshot()
    st.session_state.snapshot_time = time.time()
    st.rerun()
