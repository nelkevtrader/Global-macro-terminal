import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal")

API = "https://global-macro-terminal-1.onrender.com/global-state"

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

# ----------------------------
# LOAD DATA
# ----------------------------
data = requests.get(API).json()

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency","Stress"])
df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# ----------------------------
# FORMAT
# ----------------------------
df["Stress (%)"] = (df["Stress"] * 100).round(2)
df["Delta (%)"] = (df["Stress"].diff().fillna(0) * 100).round(2)

# ----------------------------
# REAL FX DATA (CORRECTED)
# ----------------------------
@st.cache_data(ttl=300)
def get_fx():
    try:
        return requests.get("https://open.er-api.com/v6/latest/USD").json()["rates"]
    except:
        return {}

fx = get_fx()

def fx_move(currency):
    if currency in fx and fx[currency] > 0:
        # normalized deviation
        val = abs(np.log(fx[currency])) * 10
        return min(val, 100)
    return 0

df["FX Move (%)"] = df["Currency"].apply(fx_move).round(2)

# ----------------------------
# BTC + GOLD (FIXED)
# ----------------------------
@st.cache_data(ttl=60)
def get_btc():
    try:
        return requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids":"bitcoin","vs_currencies":"usd"},
            timeout=10
        ).json()["bitcoin"]["usd"]
    except:
        return None

@st.cache_data(ttl=300)
def get_gold():
    try:
        data = requests.get("https://api.metals.live/v1/spot").json()
        for item in data:
            if "gold" in item:
                return item["gold"]
    except:
        return None

btc = get_btc()
gold = get_gold()

# ----------------------------
# SIGNAL MODEL (NORMALIZED)
# ----------------------------
df["Signal (%)"] = (
    df["Stress (%)"] * 0.6 +
    abs(df["Delta (%)"]) * 0.25 +
    df["FX Move (%)"] * 0.15
)

df["Signal (%)"] = df["Signal (%)"].clip(0,100).round(2)

# ----------------------------
# CRASH RISK (FIXED)
# ----------------------------
def crash(row):
    if row["Signal (%)"] > 75:
        return "🔴 High Risk"
    elif row["Signal (%)"] > 60:
        return "🟠 Warning"
    elif row["Signal (%)"] > 40:
        return "🟡 Elevated"
    return "🟢 Stable"

df["Crash Risk"] = df.apply(crash, axis=1)

# ----------------------------
# ALERTS
# ----------------------------
alerts = df[df["Crash Risk"] == "🔴 High Risk"]

if not alerts.empty:
    st.error("🚨 HIGH CRASH RISK DETECTED")
    st.dataframe(alerts[["Label","Signal (%)"]], use_container_width=True)

# ----------------------------
# HEADER
# ----------------------------
c1,c2,c3 = st.columns(3)

with c1:
    st.metric("Bitcoin", f"${btc:,}" if btc else "Unavailable")

with c2:
    st.metric("Gold", f"${gold}" if gold else "Unavailable")

with c3:
    st.metric("Regime", data["regime"])

st.divider()

# ----------------------------
# EXPLANATIONS
# ----------------------------
with st.expander("ℹ️ Column Explanations"):
    st.write("""
    Stress (%) → macro stress baseline  
    Delta (%) → change in stress  
    FX Move (%) → currency pressure vs USD  
    Signal (%) → combined risk score (0–100)  
    Crash Risk → probability classification  
    """)

# ----------------------------
# TOP RISK
# ----------------------------
st.subheader("🚨 Highest Risk Countries")

top = df.sort_values("Signal (%)", ascending=False).head(5)

st.dataframe(
    top[["Label","Stress (%)","Signal (%)","Crash Risk"]]
    .reset_index(drop=True),
    use_container_width=True
)

# ----------------------------
# FULL TABLE
# ----------------------------
st.subheader("🌍 Global Macro Table")

display = df[[
    "Label","Stress (%)","Delta (%)","FX Move (%)","Signal (%)","Crash Risk"
]]

st.dataframe(display.reset_index(drop=True), use_container_width=True)

# ----------------------------
# MOMENTUM
# ----------------------------
st.subheader("📈 Stress Momentum")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)"]]
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
