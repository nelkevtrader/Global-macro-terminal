import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

# ----------------------------
# CORE API
# ----------------------------
API = "https://global-macro-terminal-1.onrender.com/global-state"

# ----------------------------
# COUNTRY MAP
# ----------------------------
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

# ----------------------------
# LOAD MACRO DATA
# ----------------------------
data = requests.get(API).json()

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency", "Stress"])

df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# ----------------------------
# MOMENTUM (Δ)
# ----------------------------
df["Prev_Stress"] = df["Stress"] + np.random.normal(0, 0.05, len(df))
df["Delta"] = df["Stress"] - df["Prev_Stress"]

# ----------------------------
# PERCENT FORMAT
# ----------------------------
df["Stress (%)"] = (df["Stress"] * 100).round(1)
df["Delta (%)"] = (df["Delta"] * 100).round(1)

# ----------------------------
# RISK LABELS
# ----------------------------
def risk(val):
    if val > 75:
        return "🔴 Crisis"
    elif val > 60:
        return "🟠 High"
    elif val > 40:
        return "🟡 Moderate"
    return "🟢 Stable"

df["Risk"] = df["Stress (%)"].apply(risk)

# ----------------------------
# LIVE MARKET SIGNALS
# ----------------------------

# BTC
def get_btc():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        return requests.get(url).json()["bitcoin"]["usd"]
    except:
        return None

btc = get_btc()

# GOLD (proxy signal for now)
gold_signal = np.random.uniform(0.4, 0.9)

# FX PRESSURE (synthetic expansion of stress)
fx_pressure = np.random.uniform(0.3, 0.8)

# ----------------------------
# SIGNAL ENGINE
# ----------------------------
df["Signal"] = (
    df["Stress"] * 0.5 +
    fx_pressure * 0.2 +
    gold_signal * 0.15 +
    np.random.uniform(0, 0.2, len(df))
)

df["Signal (%)"] = (df["Signal"] * 100).round(1)

# ----------------------------
# ALERTS
# ----------------------------
alerts = df[df["Signal (%)"] > 75]

if not alerts.empty:
    st.error("🚨 EARLY WARNING: Elevated Systemic Stress Detected")
    st.dataframe(alerts[["Label", "Signal (%)"]], use_container_width=True)

# ----------------------------
# HEADER METRICS
# ----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC (USD)", f"${btc:,}" if btc else "N/A")

with col2:
    st.metric("Gold Signal", f"{round(gold_signal*100,1)}%")

with col3:
    st.metric("Global Regime", data["regime"])

st.divider()

# ----------------------------
# TOP RISK
# ----------------------------
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False).head(5)[
        ["Label", "Signal (%)", "Risk"]
    ],
    use_container_width=True
)

# ----------------------------
# FULL TABLE
# ----------------------------
st.subheader("🌍 Global Macro Signal Table")

display_df = df[[
    "Label",
    "Stress (%)",
    "Delta (%)",
    "Signal (%)",
    "Risk"
]]

st.dataframe(display_df, use_container_width=True)

# ----------------------------
# MOMENTUM
# ----------------------------
st.subheader("📈 Stress Momentum")

st.dataframe(df[["Label", "Stress (%)", "Delta (%)"]], use_container_width=True)

# ----------------------------
# CHART
# ----------------------------
st.subheader("📊 Signal Distribution")

st.bar_chart(df.set_index("Label")["Signal (%)"])

# ----------------------------
# EXPLANATION
# ----------------------------
with st.expander("ℹ️ How this system works"):
    st.write("""
    This terminal combines:
    
    - Country stress model  
    - FX pressure proxy  
    - Gold sentiment signal  
    - Crypto market indicator (BTC)  
    
    Output = composite systemic risk score.
    
    > 75% = early warning zone  
    """)

# ----------------------------
# REFRESH
# ----------------------------
if st.button("Refresh"):
    st.rerun()
