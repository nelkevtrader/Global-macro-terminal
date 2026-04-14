import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal")

API = "https://global-macro-terminal-1.onrender.com/global-state"

# =========================
# SAFE REQUEST FUNCTION
# =========================
def safe_get(url, params=None, retries=3):
    for _ in range(retries):
        try:
            r = requests.get(url, params=params, timeout=5)
            if r.status_code == 200:
                return r
        except:
            time.sleep(1)
    return None

# =========================
# COUNTRY MAP
# =========================
currency_map = {
    "EGP": "Egypt","TRY": "Turkey","ARS": "Argentina",
    "NGN": "Nigeria","ZAR": "South Africa","PKR": "Pakistan",
    "LKR": "Sri Lanka","GHS": "Ghana","KES": "Kenya",
    "USD": "United States","EUR": "Eurozone","JPY": "Japan",
    "GBP": "United Kingdom","CNY": "China","INR": "India",
    "BRL": "Brazil","MXN": "Mexico","RUB": "Russia",
    "IDR": "Indonesia","VND": "Vietnam"
}

# =========================
# LOAD MACRO DATA
# =========================
resp = safe_get(API)
data = resp.json() if resp else {"countries": {}, "regime": "Unknown"}

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency","Stress"])

df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# =========================
# FORMAT
# =========================
df["Stress (%)"] = (df["Stress"] * 100).round(2)
df["Delta (%)"] = (df["Stress"].diff().fillna(0) * 100).round(2)

# =========================
# FX DATA (RESILIENT)
# =========================
@st.cache_data(ttl=300)
def get_fx():
    r = safe_get("https://open.er-api.com/v6/latest/USD")
    if r:
        try:
            return r.json()["rates"]
        except:
            pass
    return {}

fx = get_fx()

def fx_move(currency):
    try:
        val = fx.get(currency, 1)
        move = abs(np.log(val)) * 10
        return min(move, 100)
    except:
        return 0

df["FX Move (%)"] = df["Currency"].apply(fx_move).round(2)

# =========================
# BTC (RESILIENT)
# =========================
@st.cache_data(ttl=60)
def get_btc():
    urls = [
        ("https://api.coingecko.com/api/v3/simple/price", {"ids":"bitcoin","vs_currencies":"usd"}),
        ("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", None)
    ]

    for url, params in urls:
        r = safe_get(url, params)
        if r:
            try:
                data = r.json()
                if "bitcoin" in data:
                    return float(data["bitcoin"]["usd"])
                if "price" in data:
                    return float(data["price"])
            except:
                continue

    return 30000.0  # fallback

# =========================
# GOLD (RESILIENT)
# =========================
@st.cache_data(ttl=300)
def get_gold():
    # Primary
    r = safe_get("https://api.metals.live/v1/spot")
    if r:
        try:
            data = r.json()
            for item in data:
                if isinstance(item, dict) and "gold" in item:
                    return float(item["gold"])
        except:
            pass

    # Backup (Stooq)
    r = safe_get("https://stooq.com/q/l/?s=xauusd&i=d")
    if r:
        try:
            row = r.text.split("\n")[1].split(",")
            return float(row[3])
        except:
            pass

    return 2000.0  # final fallback

btc = get_btc()
gold = get_gold()

# =========================
# SIGNAL MODEL (STABLE)
# =========================
df["Signal (%)"] = (
    df["Stress (%)"] * 0.6 +
    abs(df["Delta (%)"]) * 0.25 +
    df["FX Move (%)"] * 0.15
)

df["Signal (%)"] = df["Signal (%)"].clip(0,100).round(2)

# =========================
# CRASH RISK
# =========================
def crash(val):
    if val > 75:
        return "🔴 High Risk"
    elif val > 60:
        return "🟠 Warning"
    elif val > 40:
        return "🟡 Elevated"
    return "🟢 Stable"

df["Crash Risk"] = df["Signal (%)"].apply(crash)

# =========================
# ALERTS
# =========================
alerts = df[df["Crash Risk"] == "🔴 High Risk"]

if not alerts.empty:
    st.error("🚨 HIGH CRASH RISK DETECTED")
    st.dataframe(alerts[["Label","Signal (%)"]], use_container_width=True)

# =========================
# HEADER
# =========================
c1,c2,c3 = st.columns(3)

with c1:
    st.metric("Bitcoin", f"${btc:,.0f}")

with c2:
    st.metric("Gold", f"${gold:,.0f}")

with c3:
    st.metric("Regime", data["regime"])

st.divider()

# =========================
# EXPLANATIONS
# =========================
with st.expander("ℹ️ Column Explanations"):
    st.write("""
    Stress (%) → macro stress baseline  
    Delta (%) → change in stress  
    FX Move (%) → currency pressure vs USD  
    Signal (%) → combined risk score (0–100)  
    Crash Risk → probability classification  
    """)

# =========================
# TOP RISK
# =========================
st.subheader("🚨 Highest Risk Countries")

top = df.sort_values("Signal (%)", ascending=False).head(5)

st.dataframe(
    top[["Label","Stress (%)","Signal (%)","Crash Risk"]]
    .reset_index(drop=True),
    use_container_width=True
)

# =========================
# FULL TABLE
# =========================
st.subheader("🌍 Global Macro Table")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)","FX Move (%)","Signal (%)","Crash Risk"]]
    .reset_index(drop=True),
    use_container_width=True
)

# =========================
# MOMENTUM
# =========================
st.subheader("📈 Stress Momentum")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)"]]
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
