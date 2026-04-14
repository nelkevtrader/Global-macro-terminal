import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal — Data Reconciled")

API = "https://global-macro-terminal-1.onrender.com/global-state"

# =========================
# SAFE REQUEST
# =========================
def safe_get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# =========================
# RECONCILIATION ENGINE
# =========================
def reconcile(values, tolerance=0.25):
    """
    Takes multiple numeric sources and:
    - removes None
    - checks spread
    - returns median + confidence
    """
    vals = [v for v in values if v is not None]
    if len(vals) == 0:
        return None, 0.0, "NO DATA"

    median = np.median(vals)
    spread = (max(vals) - min(vals)) / median if median != 0 else 1

    if spread < tolerance:
        confidence = "HIGH"
    elif spread < 0.6:
        confidence = "MEDIUM"
    else:
        confidence = "LOW (DATA CONFLICT)"

    return float(median), spread, confidence

# =========================
# LOAD MACRO DATA
# =========================
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
df["Delta (%)"] = df["Stress"].diff().fillna(0) * 100

# =========================
# FX (single source + sanity band)
# =========================
fx_raw = safe_get("https://open.er-api.com/v6/latest/USD")
fx = fx_raw["rates"] if fx_raw else {}

def fx_move(currency):
    v = fx.get(currency)
    if not v:
        return None
    move = abs(np.log(v)) * 10
    return min(move, 100)

df["FX Move (%)"] = df["Currency"].apply(fx_move)

# =========================
# BTC (multi-source reconciliation)
# =========================
def get_btc_sources():
    c1 = safe_get("https://api.coingecko.com/api/v3/simple/price", {"ids":"bitcoin","vs_currencies":"usd"})
    c2 = safe_get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")

    v1 = None
    v2 = None

    try:
        v1 = c1["bitcoin"]["usd"]
    except:
        pass

    try:
        v2 = float(c2["price"])
    except:
        pass

    return reconcile([v1, v2])

btc_price, btc_spread, btc_conf = get_btc_sources()

# =========================
# GOLD (multi-source reconciliation)
# =========================
def get_gold_sources():
    v1 = None
    v2 = None

    # -------------------------
    # SOURCE 1: Yahoo Finance
    # -------------------------
    try:
        url = "https://query1.finance.yahoo.com/v7/finance/quote"
        r = requests.get(url, params={"symbols": "GC=F"}, timeout=5)
        data = r.json()

        result = data.get("quoteResponse", {}).get("result", [])
        if result:
            v1 = float(result[0].get("regularMarketPrice"))
    except:
        pass

    # -------------------------
    # SOURCE 2: Stooq (backup)
    # -------------------------
    try:
        r = requests.get("https://stooq.com/q/l/?s=xauusd&i=d", timeout=5)
        lines = r.text.split("\n")

        if len(lines) > 1:
            parts = lines[1].split(",")
            v2 = float(parts[3])  # Close price
    except:
        pass

    # IMPORTANT: return AFTER both sources
    return reconcile([v1, v2])
    # -------------------------
    # SOURCE 2: Stooq (very stable)
    # -------------------------
    try:
        r = requests.get("https://stooq.com/q/l/?s=xauusd&i=d", timeout=5)
        lines = r.text.split("\n")

        if len(lines) > 1:
            parts = lines[1].split(",")
            v2 = float(parts[3])  # Close price
    except:
        pass

    return reconcile([v1, v2])

gold_price, gold_spread, gold_conf = get_gold_sources()

# =========================
# SIGNAL MODEL
# =========================
df["Signal (%)"] = (
    df["Stress (%)"] * 0.65 +
    abs(df["Delta (%)"]) * 0.2 +
    df["FX Move (%)"].fillna(0) * 0.15
)

df["Signal (%)"] = df["Signal (%)"].clip(0,100).round(2)

# =========================
# RISK
# =========================
def risk(x):
    if x > 75:
        return "🔴 High Risk"
    elif x > 60:
        return "🟠 Warning"
    elif x > 40:
        return "🟡 Elevated"
    return "🟢 Stable"

df["Risk"] = df["Signal (%)"].apply(risk)

# =========================
# DATA QUALITY PANEL
# =========================
st.subheader("🧠 Data Reconciliation Layer")

st.write("### BTC")
st.write(f"Price: {btc_price}")
st.write(f"Spread: {btc_spread:.2f}")
st.write(f"Confidence: {btc_conf}")

st.write("### GOLD")
st.write(f"Price: {gold_price}")
st.write(f"Spread: {gold_spread:.2f}")
st.write(f"Confidence: {gold_conf}")

st.divider()

# =========================
# HEADER
# =========================
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Bitcoin", f"${btc_price:,.0f}" if btc_price else "N/A")

with c2:
    st.metric("Gold", f"${gold_price:,.0f}" if gold_price else "N/A")

with c3:
    st.metric("Regime", data["regime"])

st.divider()

# =========================
# TOP RISK
# =========================
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False)
    [["Label","Stress (%)","Signal (%)","Risk"]]
    .head(5)
    .reset_index(drop=True),
    use_container_width=True
)

# =========================
# FULL TABLE
# =========================
st.subheader("🌍 Global Macro Table")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)","FX Move (%)","Signal (%)","Risk"]]
    .reset_index(drop=True),
    use_container_width=True
)

# =========================
# CHART
# =========================
st.subheader("📊 Signal Distribution")
st.bar_chart(df.set_index("Label")["Signal (%)"])

# =========================
# REFRESH
# =========================
if st.button("Refresh"):
    st.rerun()
