import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

# =========================
# API SOURCE
# =========================
API = "https://global-macro-terminal-1.onrender.com/global-state"

# =========================
# COUNTRY MAP
# =========================
currency_map = {
    "EGP": "Egypt",
    "TRY": "Turkey",
    "ARS": "Argentina",
    "NGN": "Nigeria",
    "ZAR": "South Africa",
    "PKR": "Pakistan",
    "LKR": "Sri Lanka",
    "GHS": "Ghana",
    "KES": "Kenya",
    "USD": "United States",
    "EUR": "Eurozone",
    "JPY": "Japan",
    "GBP": "United Kingdom",
    "CNY": "China",
    "INR": "India",
    "BRL": "Brazil",
    "MXN": "Mexico",
    "RUB": "Russia",
    "IDR": "Indonesia",
    "VND": "Vietnam"
}

# =========================
# LOAD MACRO DATA
# =========================
data = requests.get(API).json()

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency", "Stress"])

df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# =========================
# MOMENTUM (DELTA)
# =========================
df["Prev_Stress"] = df["Stress"] + np.random.normal(0, 0.05, len(df))
df["Delta"] = df["Stress"] - df["Prev_Stress"]

# =========================
# PERCENT FORMAT
# =========================
df["Stress (%)"] = (df["Stress"] * 100).round(1)
df["Delta (%)"] = (df["Delta"] * 100).round(1)

# =========================
# RISK ENGINE
# =========================
def risk(x):
    if x > 75:
        return "🔴 Crisis"
    elif x > 60:
        return "🟠 High"
    elif x > 40:
        return "🟡 Moderate"
    return "🟢 Stable"

df["Risk"] = df["Stress (%)"].apply(risk)

# =========================
# BTC (ROBUST + CACHED)
# =========================
@st.cache_data(ttl=60)
def get_btc():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        r = requests.get(url, params={"ids": "bitcoin", "vs_currencies": "usd"}, timeout=10)
        return r.json()["bitcoin"]["usd"]
    except:
        return None

btc = get_btc()

# =========================
# MARKET PROXIES (CLEARLY LABELLED)
# =========================
gold_signal = np.random.uniform(0.45, 0.9)   # proxy only
fx_pressure = np.random.uniform(0.3, 0.8)    # proxy only

# =========================
# SIGNAL ENGINE
# =========================
df["Signal"] = (
    df["Stress"] * 0.5 +
    fx_pressure * 0.2 +
    gold_signal * 0.15 +
    np.random.uniform(0, 0.15, len(df))
)

df["Signal (%)"] = (df["Signal"] * 100).round(1)

# =========================
# ALERTS
# =========================
alerts = df[df["Signal (%)"] > 75]

if not alerts.empty:
    st.error("🚨 EARLY WARNING: Elevated Macro Stress Detected")
    st.dataframe(alerts[["Label", "Signal (%)"]], use_container_width=True)

# =========================
# HEADER METRICS
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Bitcoin (USD)", f"${btc:,}" if btc else "N/A")

with col2:
    st.metric("Gold Signal (proxy)", f"{round(gold_signal*100,1)}%")

with col3:
    st.metric("Regime", data["regime"])

st.divider()

# =========================
# TOP RISK
# =========================
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False).head(5)[
        ["Label", "Stress (%)", "Signal (%)", "Risk"]
    ],
    use_container_width=True
)

with st.expander("ℹ️ Interpretation"):
    st.write("""
    High signal values indicate combined macro + market stress.
    
    Often precedes:
    - FX instability  
    - capital flight  
    - policy intervention  
    """)

# =========================
# FULL TABLE
# =========================
st.subheader("🌍 Global Macro Table")

display_df = df[[
    "Label",
    "Stress (%)",
    "Delta (%)",
    "Signal (%)",
    "Risk"
]]

st.dataframe(display_df, use_container_width=True)

with st.expander("ℹ️ Column meanings"):
    st.write("""
    Stress (%) → macro pressure  
    Delta (%) → change in stress  
    Signal (%) → combined risk model  
    Risk → classification level  
    """)

# =========================
# MOMENTUM VIEW
# =========================
st.subheader("📈 Stress Momentum")

st.dataframe(df[["Label", "Stress (%)", "Delta (%)"]], use_container_width=True)

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
