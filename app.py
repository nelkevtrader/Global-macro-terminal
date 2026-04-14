import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal (Stable + Reconciled)")

API = "https://global-macro-terminal-1.onrender.com/global-state"

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
# RECONCILIATION ENGINE
# =========================================================
def reconcile(values):
    vals = [v for v in values if isinstance(v, (int, float))]

    if len(vals) == 0:
        return None, None, "NO DATA"

    median = float(np.median(vals))

    if len(vals) > 1:
        spread = float(np.std(vals) / median)
    else:
        spread = 0.0

    if spread < 0.01:
        conf = "HIGH"
    elif spread < 0.05:
        conf = "MEDIUM"
    else:
        conf = "LOW (DISAGREEMENT)"

    return median, spread, conf

# =========================================================
# LOAD MACRO DATA
# =========================================================
data = safe_get(API) or {"countries": {}, "regime": "Unknown"}

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

df = df.sort_values("Stress", ascending=False)

df["Stress (%)"] = (df["Stress"] * 100).round(2)
df["Delta (%)"] = (df["Stress"].diff().fillna(0) * 100).round(2)

# =========================================================
# FX MOVE
# =========================================================
fx_raw = safe_get("https://open.er-api.com/v6/latest/USD")
fx = fx_raw["rates"] if fx_raw else {}

def fx_move(currency):
    val = fx.get(currency)
    if not val:
        return None
    return min(abs(np.log(val)) * 10, 100)

df["FX Move (%)"] = df["Currency"].apply(fx_move)

# =========================================================
# BTC (2 SOURCES)
# =========================================================
def get_btc():
    v1 = None
    v2 = None

    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=6
        )
        v1 = r.json()["bitcoin"]["usd"]
    except:
        pass

    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            timeout=6
        )
        v2 = float(r.json()["price"])
    except:
        pass

    return reconcile([v1, v2])

btc_price, btc_spread, btc_conf = get_btc()

# =========================================================
# GOLD (FIXED PROPERLY - NO FAKE VALUES)
# =========================================================
def get_gold():
    v1 = None
    v2 = None

    # Yahoo Finance (GC=F)
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

    # Stooq fallback
    try:
        r = requests.get("https://stooq.com/q/l/?s=xauusd&i=d", timeout=6)
        line = r.text.split("\n")[1].split(",")
        v2 = float(line[3])
    except:
        pass

    return reconcile([v1, v2])

gold_price, gold_spread, gold_conf = get_gold()

# =========================================================
# SIGNAL MODEL
# =========================================================
df["Signal (%)"] = (
    df["Stress (%)"] * 0.65 +
    df["Delta (%)"].abs() * 0.2 +
    df["FX Move (%)"].fillna(0) * 0.15
)

df["Signal (%)"] = df["Signal (%)"].clip(0, 100).round(2)

# =========================================================
# RISK MODEL
# =========================================================
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

st.divider()

# =========================================================
# DATA QUALITY PANEL
# =========================================================
st.subheader("🧠 Data Reconciliation Layer")

st.write("### BTC")
st.write(f"Price: {btc_price}")
st.write(f"Spread: {btc_spread}")
st.write(f"Confidence: {btc_conf}")

st.write("### GOLD")
st.write(f"Price: {gold_price}")
st.write(f"Spread: {gold_spread}")
st.write(f"Confidence: {gold_conf}")

st.divider()

# =========================================================
# TOP RISK
# =========================================================
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False)
    [["Label","Stress (%)","Signal (%)","Risk"]]
    .head(5)
    .reset_index(drop=True),
    use_container_width=True
)

# =========================================================
# FULL TABLE
# =========================================================
st.subheader("🌍 Global Macro Table")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)","FX Move (%)","Signal (%)","Risk"]]
    .reset_index(drop=True),
    use_container_width=True
)

# =========================================================
# CHART
# =========================================================
st.subheader("📊 Signal Distribution")
st.bar_chart(df.set_index("Label")["Signal (%)"])

# =========================================================
# REFRESH
# =========================================================
if st.button("Refresh"):
    st.rerun()
