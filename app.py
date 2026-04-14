import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal (Real + Predictive)")

API = "https://global-macro-terminal-1.onrender.com/global-state"

# ----------------------------
# COUNTRY MAP
# ----------------------------
currency_map = {
    "EGP": "Egypt", "TRY": "Turkey", "ARS": "Argentina",
    "NGN": "Nigeria", "ZAR": "South Africa", "PKR": "Pakistan",
    "LKR": "Sri Lanka", "GHS": "Ghana", "KES": "Kenya",
    "USD": "United States", "EUR": "Eurozone", "JPY": "Japan",
    "GBP": "United Kingdom", "CNY": "China", "INR": "India",
    "BRL": "Brazil", "MXN": "Mexico", "RUB": "Russia",
    "IDR": "Indonesia", "VND": "Vietnam"
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
# REAL FX DATA
# ----------------------------
@st.cache_data(ttl=300)
def get_fx():
    try:
        return requests.get("https://open.er-api.com/v6/latest/USD").json()["rates"]
    except:
        return {}

fx = get_fx()

def fx_move(currency):
    if currency in fx:
        return abs(1 - fx[currency]) * 100
    return 0

df["FX Move (%)"] = df["Currency"].apply(fx_move).round(2)

# ----------------------------
# MOMENTUM
# ----------------------------
df["Delta (%)"] = (df["Stress"].diff().fillna(0) * 100).round(2)
df["Stress (%)"] = (df["Stress"] * 100).round(2)

# ----------------------------
# SIGNAL MODEL (FIXED)
# ----------------------------
df["Signal (%)"] = (
    df["Stress (%)"] * 0.5 +
    df["Delta (%)"].abs() * 0.25 +
    df["FX Move (%)"] * 0.25
).round(2)

# ----------------------------
# CRASH PREDICTION
# ----------------------------
def crash_flag(row):
    if row["Stress (%)"] > 70 and row["Delta (%)"] > 5 and row["FX Move (%)"] > 10:
        return "🔴 High Risk"
    elif row["Stress (%)"] > 60 and row["Delta (%)"] > 2:
        return "🟠 Warning"
    return "🟢 Stable"

df["Crash Risk"] = df.apply(crash_flag, axis=1)

# ----------------------------
# BTC + GOLD (REAL)
# ----------------------------
@st.cache_data(ttl=60)
def get_btc():
    try:
        return requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"}
        ).json()["bitcoin"]["usd"]
    except:
        return None

@st.cache_data(ttl=300)
def get_gold():
    try:
        data = requests.get("https://api.metals.live/v1/spot").json()
        for x in data:
            if "gold" in x:
                return x["gold"]
    except:
        return None

btc = get_btc()
gold = get_gold()

# ----------------------------
# HEADER
# ----------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Bitcoin", f"${btc:,}" if btc else "N/A")

with c2:
    st.metric("Gold", f"${gold}" if gold else "N/A")

with c3:
    st.metric("Regime", data["regime"])

st.divider()

# ----------------------------
# COLUMN EXPLANATIONS (FIXED)
# ----------------------------
with st.expander("ℹ️ Column Explanations"):
    st.write("""
    **Stress (%)** → baseline macro stress  
    **Delta (%)** → change in stress (momentum)  
    **FX Move (%)** → currency deviation vs USD  
    **Signal (%)** → combined risk score  
    **Crash Risk** → probability of instability  
    """)

# ----------------------------
# TOP RISK (FIXED SORT)
# ----------------------------
st.subheader("🚨 Highest Risk Countries")

top = df.sort_values("Signal (%)", ascending=False).head(5)

st.dataframe(
    top[["Label", "Stress (%)", "Signal (%)", "Crash Risk"]]
    .reset_index(drop=True),
    use_container_width=True
)

# ----------------------------
# FULL TABLE
# ----------------------------
st.subheader("🌍 Global Macro Table")

display = df[[
    "Label",
    "Stress (%)",
    "Delta (%)",
    "FX Move (%)",
    "Signal (%)",
    "Crash Risk"
]]

st.dataframe(display.reset_index(drop=True), use_container_width=True)

# ----------------------------
# MOMENTUM
# ----------------------------
st.subheader("📈 Stress Momentum")

st.dataframe(
    df[["Label", "Stress (%)", "Delta (%)"]].reset_index(drop=True),
    use_container_width=True
)

# ----------------------------
# CHART
# ----------------------------
st.subheader("📊 Signal Distribution")

st.bar_chart(df.set_index("Label")["Signal (%)"])

# ----------------------------
# ALERTS
# ----------------------------
alerts = df[df["Crash Risk"] == "🔴 High Risk"]

if not alerts.empty:
    st.error("🚨 CRASH RISK DETECTED")
    st.dataframe(alerts[["Label", "Signal (%)"]], use_container_width=True)

# ----------------------------
# REFRESH
# ----------------------------
if st.button("Refresh"):
    st.rerun()
