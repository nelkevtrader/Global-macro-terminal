import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal")

# --- API ENDPOINTS ---
MACRO_API = "https://global-macro-terminal-1.onrender.com/global-state"

# --- CURRENCY MAP ---
currency_map = {
    "EGP": "Egypt",
    "TRY": "Turkey",
    "ARS": "Argentina",
    "NGN": "Nigeria",
    "ZAR": "South Africa"
}

# --- LOAD MACRO DATA ---
macro = requests.get(MACRO_API).json()
df = pd.DataFrame(list(macro["countries"].items()), columns=["Currency", "Stress"])

df["Country"] = df["Currency"].map(currency_map)
df["Label"] = df["Currency"] + " - " + df["Country"].fillna("Unknown")

df = df.sort_values(by="Stress", ascending=False)

# --- FX DATA ---
def get_fx(base="USD"):
    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        data = requests.get(url).json()
        return data["rates"]
    except:
        return {}

fx_rates = get_fx()

# --- CRYPTO DATA ---
def get_btc():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        data = requests.get(url).json()
        return data["bitcoin"]["usd"]
    except:
        return None

btc_price = get_btc()

# --- SIMULATED GOLD SIGNAL ---
gold_signal = np.random.uniform(0, 1)

# --- SIGNAL ENGINE ---
signals = []

for _, row in df.iterrows():
    fx_score = np.random.uniform(0, 1)
    crypto_score = np.random.uniform(0, 1)

    total_signal = (row["Stress"] + fx_score + crypto_score + gold_signal) / 4

    signals.append(total_signal)

df["Signal"] = signals
df["Signal (%)"] = (df["Signal"] * 100).round(1)

# --- ALERT SYSTEM ---
alerts = df[df["Signal (%)"] > 75]

if not alerts.empty:
    st.error("🚨 EARLY WARNING: Potential Currency Stress Detected")
    st.dataframe(alerts[["Label", "Signal (%)"]])

# --- GLOBAL METRICS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC Price", f"${btc_price}" if btc_price else "N/A")

with col2:
    st.metric("Gold Signal", f"{round(gold_signal*100,1)}%")

with col3:
    st.metric("Global Regime", macro["regime"])

st.divider()

# --- TOP SIGNALS ---
st.subheader("🚨 Highest Risk Signals")

top = df.sort_values(by="Signal", ascending=False).head(5)

st.dataframe(top[["Label", "Signal (%)"]], use_container_width=True)

# --- FULL TABLE ---
st.subheader("🌍 Global Signal Table")

st.dataframe(
    df[["Label", "Signal (%)"]],
    use_container_width=True
)

# --- CHART ---
st.subheader("📊 Signal Distribution")

st.bar_chart(df.set_index("Label")["Signal (%)"])

# --- EXPLANATION ---
with st.expander("ℹ️ How signals work"):
    st.write("""
    This system combines:
    
    - macro stress  
    - FX weakness  
    - crypto flows  
    - gold demand  
    
    Higher signal = higher probability of instability.
    
    > 75% = early warning  
    """)

# --- REFRESH ---
if st.button("Refresh"):
    st.rerun()
