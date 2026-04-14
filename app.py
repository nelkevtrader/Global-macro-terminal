import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal (Real Data)")

# =========================
# API
# =========================
MACRO_API = "https://global-macro-terminal-1.onrender.com/global-state"

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
data = requests.get(MACRO_API).json()

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency", "Stress"])

df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# =========================
# REAL FX DATA
# =========================
@st.cache_data(ttl=300)
def get_fx():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        return requests.get(url).json()["rates"]
    except:
        return {}

fx_rates = get_fx()

# =========================
# REAL BTC
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
# REAL GOLD (via metals API proxy)
# =========================
@st.cache_data(ttl=300)
def get_gold():
    try:
        url = "https://api.metals.live/v1/spot"
        data = requests.get(url).json()
        for item in data:
            if "gold" in item:
                return item["gold"]
    except:
        return None

gold = get_gold()

# =========================
# MOMENTUM (REAL PROXY)
# =========================
df["Delta (%)"] = (df["Stress"].diff().fillna(0) * 100).round(1)
df["Stress (%)"] = (df["Stress"] * 100).round(1)

# =========================
# FX MOVEMENT SIGNAL
# =========================
def fx_signal(currency):
    try:
        if currency in fx_rates:
            return abs(1 - fx_rates[currency]) * 100
        return 0
    except:
        return 0

df["FX Signal"] = df["Currency"].apply(fx_signal)

# =========================
# GOLD + BTC SIGNALS
# =========================
gold_signal = 0 if not gold else min(100, (gold / 2000) * 100)
btc_signal = 0 if not btc else min(100, (btc / 100000) * 100)

# =========================
# FINAL SIGNAL ENGINE (REAL)
# =========================
df["Signal (%)"] = (
    df["Stress (%)"] * 0.5 +
    df["FX Signal"] * 0.3 +
    gold_signal * 0.1 +
    btc_signal * 0.1
).round(1)

# =========================
# RISK LABEL
# =========================
def risk(val):
    if val > 75:
        return "🔴 Crisis"
    elif val > 60:
        return "🟠 High"
    elif val > 40:
        return "🟡 Moderate"
    return "🟢 Stable"

df["Risk"] = df["Signal (%)"].apply(risk)

# =========================
# ALERTS
# =========================
alerts = df[df["Signal (%)"] > 75]

if not alerts.empty:
    st.error("🚨 EARLY WARNING: Real Market Stress Detected")
    st.dataframe(alerts[["Label", "Signal (%)"]], use_container_width=True)

# =========================
# HEADER
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Bitcoin", f"${btc:,}" if btc else "N/A")

with col2:
    st.metric("Gold (USD)", f"${gold}" if gold else "N/A")

with col3:
    st.metric("Regime", data["regime"])

st.divider()

# =========================
# TOP RISK
# =========================
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False)
    [["Label", "Stress (%)", "Signal (%)", "Risk"]]
    .head(5)
    .reset_index(drop=True),
    use_container_width=True
)

# =========================
# FULL TABLE
# =========================
st.subheader("🌍 Global Macro Table")

display = df[[
    "Label",
    "Stress (%)",
    "Delta (%)",
    "FX Signal",
    "Signal (%)",
    "Risk"
]]

st.dataframe(display.reset_index(drop=True), use_container_width=True)

# =========================
# MOMENTUM
# =========================
st.subheader("📈 Stress Momentum")

st.dataframe(
    df[["Label", "Stress (%)", "Delta (%)"]]
    .reset_index(drop=True),
    use_container_width=True
)

# =========================
# CHART
# =========================
st.subheader("📊 Signal Distribution")

st.bar_chart(df.set_index("Label")["Signal (%)"])

# =========================
# INFO
# =========================
with st.expander("ℹ️ How this works"):
    st.write("""
    This system now uses REAL DATA:
    
    - Macro stress model  
    - Live FX rates  
    - Bitcoin price  
    - Gold price  
    
    Signal = combined real-world stress indicator.
    """)

# =========================
# REFRESH
# =========================
if st.button("Refresh"):
    st.rerun()
