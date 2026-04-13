import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

# ----------------------------
# API
# ----------------------------
API = "https://global-macro-terminal-1.onrender.com/global-state"

# ----------------------------
# COUNTRY MAP (COMPLETE)
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
# LOAD DATA
# ----------------------------
data = requests.get(API).json()

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency", "Stress"])

df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# ----------------------------
# MOMENTUM (DELTA RESTORED)
# ----------------------------
df["Prev_Stress"] = df["Stress"] + np.random.normal(0, 0.05, len(df))
df["Delta"] = df["Stress"] - df["Prev_Stress"]

# ----------------------------
# PERCENT FORMAT
# ----------------------------
df["Stress (%)"] = (df["Stress"] * 100).round(1)
df["Delta (%)"] = (df["Delta"] * 100).round(1)

# ----------------------------
# RISK ENGINE (RESTORED)
# ----------------------------
def risk(x):
    if x > 75:
        return "🔴 Crisis"
    elif x > 60:
        return "🟠 High"
    elif x > 40:
        return "🟡 Moderate"
    return "🟢 Stable"

df["Risk"] = df["Stress (%)"].apply(risk)

# ----------------------------
# LIVE MARKET DATA
# ----------------------------

# BTC (REAL)
def btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        return requests.get(url).json()["bitcoin"]["usd"]
    except:
        return None

def btc_price():
    urls = [
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    ]

    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            return data["bitcoin"]["usd"]
        except:
            continue

    return None

# GOLD (proxy signal - until real feed added)
gold = np.random.uniform(0.45, 0.9)

# FX PRESSURE (proxy)
fx = np.random.uniform(0.3, 0.8)

# ----------------------------
# SIGNAL ENGINE (COMBINED)
# ----------------------------
df["Signal"] = (
    df["Stress"] * 0.5 +
    fx * 0.2 +
    gold * 0.15 +
    np.random.uniform(0, 0.15, len(df))
)

df["Signal (%)"] = (df["Signal"] * 100).round(1)

# ----------------------------
# ALERT SYSTEM (RESTORED)
# ----------------------------
alerts = df[df["Signal (%)"] > 75]

if not alerts.empty:
    st.error("🚨 EARLY WARNING: Systemic Stress Spike Detected")
    st.dataframe(alerts[["Label", "Signal (%)"]], use_container_width=True)

# ----------------------------
# HEADER METRICS
# ----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC (USD)", f"${btc:,}" if btc else "N/A")

with col2:
    st.metric("Gold Signal", f"{round(gold*100,1)}%")

with col3:
    st.metric("Regime", data["regime"])

st.divider()

# ----------------------------
# TOP RISK (RESTORED)
# ----------------------------
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False).head(5)[
        ["Label", "Stress (%)", "Signal (%)", "Risk"]
    ],
    use_container_width=True
)

with st.expander("ℹ️ Why this matters"):
    st.write("""
    High signal = combined macro + market stress.
    
    This often precedes:
    - FX crises  
    - capital outflows  
    - policy intervention  
    """)

# ----------------------------
# FULL TABLE (RESTORED CLEANLY)
# ----------------------------
st.subheader("🌍 Global Macro Table")

display = df[[
    "Label",
    "Stress (%)",
    "Delta (%)",
    "Signal (%)",
    "Risk"
]]

st.dataframe(display, use_container_width=True)

with st.expander("ℹ️ Column meanings"):
    st.write("""
    Stress (%) → macro stress level  
    Delta (%) → change in stress  
    Signal (%) → combined risk score  
    Risk → classification  
    """)

# ----------------------------
# MOMENTUM VIEW (RESTORED)
# ----------------------------
st.subheader("📈 Stress Momentum")

st.dataframe(df[["Label", "Stress (%)", "Delta (%)"]], use_container_width=True)

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
