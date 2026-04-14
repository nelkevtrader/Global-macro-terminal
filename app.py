import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal")

API = "https://global-macro-terminal-1.onrender.com/global-state"

# ----------------------------
# SAFE REQUEST
# ----------------------------
def safe_get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# ----------------------------
# LOAD MACRO DATA
# ----------------------------
data = safe_get(API) or {"countries": {}, "regime": "Unknown"}

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency", "Stress"])

# ----------------------------
# COUNTRY MAP
# ----------------------------
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

df = df.sort_values(by="Stress", ascending=False)

# ----------------------------
# BASIC METRICS
# ----------------------------
df["Stress (%)"] = (df["Stress"] * 100).round(1)

# Simple momentum (no fake randomness)
df["Delta (%)"] = df["Stress (%)"].diff().fillna(0).round(1)

# ----------------------------
# FX DATA (STABLE USE)
# ----------------------------
@st.cache_data(ttl=300)
def get_fx():
    data = safe_get("https://open.er-api.com/v6/latest/USD")
    return data["rates"] if data else {}

fx = get_fx()

def fx_move(currency):
    val = fx.get(currency)
    if not val:
        return 0
    # normalize around reasonable range
    move = abs(val - 1) * 100
    return min(move, 20)  # cap to avoid distortion

df["FX Move (%)"] = df["Currency"].apply(fx_move).round(1)

# ----------------------------
# BTC (CLEAN)
# ----------------------------
@st.cache_data(ttl=60)
def get_btc():
    data = safe_get(
        "https://api.coingecko.com/api/v3/simple/price",
        {"ids": "bitcoin", "vs_currencies": "usd"}
    )
    try:
        return float(data["bitcoin"]["usd"])
    except:
        return None

# ----------------------------
# GOLD (FIXED PROPERLY)
# ----------------------------
@st.cache_data(ttl=300)
def get_gold():
    data = safe_get(
        "https://query1.finance.yahoo.com/v7/finance/quote",
        {"symbols": "GC=F"}
    )
    try:
        price = data["quoteResponse"]["result"][0]["regularMarketPrice"]
        if 1500 < price < 3000:
            return float(price)
    except:
        pass
    return None

btc = get_btc()
gold = get_gold()

# ----------------------------
# SIGNAL (SIMPLE + REALISTIC)
# ----------------------------
df["Signal (%)"] = (
    df["Stress (%)"] * 0.7 +
    abs(df["Delta (%)"]) * 0.2 +
    df["FX Move (%)"] * 0.1
).round(1)

df["Signal (%)"] = df["Signal (%)"].clip(0, 100)

# ----------------------------
# RISK
# ----------------------------
def risk(val):
    if val > 70:
        return "🔴 High Risk"
    elif val > 55:
        return "🟠 Warning"
    elif val > 35:
        return "🟡 Elevated"
    return "🟢 Stable"

df["Risk"] = df["Signal (%)"].apply(risk)

# ----------------------------
# HEADER
# ----------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Bitcoin", f"${btc:,.0f}" if btc else "N/A")

with c2:
    st.metric("Gold", f"${gold:,.0f}" if gold else "N/A")

with c3:
    st.metric("Regime", data["regime"])

st.divider()

# ----------------------------
# EXPLANATION
# ----------------------------
with st.expander("ℹ️ How to read this"):
    st.write("""
    Stress (%) → macro stress level  
    Delta (%) → recent change  
    FX Move (%) → currency pressure vs USD  
    Signal (%) → combined risk score  
    Risk → classification  
    """)

# ----------------------------
# TOP RISK
# ----------------------------
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False)
    [["Label", "Stress (%)", "Signal (%)", "Risk"]]
    .head(5)
    .reset_index(drop=True),
    use_container_width=True
)

# ----------------------------
# FULL TABLE
# ----------------------------
st.subheader("🌍 Global Macro Table")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)","FX Move (%)","Signal (%)","Risk"]]
    .reset_index(drop=True),
    use_container_width=True
)

# ----------------------------
# CHART
# ----------------------------
st.subheader("📊 Signal Distribution")

st.bar_chart(df.set_index("Label")["Signal (%)"])

# ----------------------------
# REFRESH
# ----------------------------
if st.button("Refresh"):
    st.rerun()
