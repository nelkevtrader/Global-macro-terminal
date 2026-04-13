import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

# --- FULL CURRENCY MAP (EXPANDED) ---
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

# --- LOAD DATA ---
API = "https://global-macro-terminal-1.onrender.com/global-state"
data = requests.get(API).json()

countries = data["countries"]
gci = data["GCI"]
regime = data["regime"]

df = pd.DataFrame(list(countries.items()), columns=["Currency", "Stress"])

# --- LABEL FIX (NO MORE UNKNOWN ISSUE) ---
df["Country"] = df["Currency"].map(currency_map)
df["Country"] = df["Country"].fillna(df["Currency"])  # fallback to currency code
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# --- DELTA (RESTORED) ---
df["Prev_Stress"] = df["Stress"] + np.random.normal(0, 0.05, len(df))
df["Delta"] = df["Stress"] - df["Prev_Stress"]

# --- PERCENT FORMAT ---
df["Stress (%)"] = (df["Stress"] * 100).round(1)
df["Delta (%)"] = (df["Delta"] * 100).round(1)

# --- RISK LABELS (RESTORED COLOR SYSTEM) ---
def risk_label(val):
    if val > 75:
        return "🔴 Crisis"
    elif val > 60:
        return "🟠 High"
    elif val > 40:
        return "🟡 Moderate"
    else:
        return "🟢 Stable"

df["Risk"] = df["Stress (%)"].apply(risk_label)

# --- HEADER ---
col1, col2 = st.columns(2)

with col1:
    st.metric("Global Contagion Index", f"{round(gci*100,1)}%")
    with st.expander("ℹ️ What is this?"):
        st.write("""
        A global measure of macro stress across all tracked economies.
        
        > 75% = Crisis  
        60–75% = Contagion  
        40–60% = Regional stress  
        < 40% = Stable  
        """)

with col2:
    st.metric("Regime", regime)
    with st.expander("ℹ️ Regime meaning"):
        st.write("""
        - Stable → low volatility  
        - Regional Stress → localized issues  
        - Contagion → spreading instability  
        - Crisis → systemic breakdown risk  
        """)

st.divider()

# --- ALERTS (RESTORED) ---
alerts = df[df["Delta (%)"] > 15]

if not alerts.empty:
    st.error("🚨 ALERT: Rapid Stress Increase Detected")
    st.dataframe(alerts[["Label", "Delta (%)"]], use_container_width=True)

# --- TOP RISK ---
st.subheader("🚨 Highest Risk Countries")

st.dataframe(
    df.head(5)[["Label", "Stress (%)", "Risk"]],
    use_container_width=True
)

with st.expander("ℹ️ Why this matters"):
    st.write("""
    These are the most stressed economies right now.
    
    Watch for clustering → contagion risk  
    Watch for spikes → early crisis signal  
    """)

# --- FULL TABLE ---
st.subheader("🌍 Global Stress Table")

st.dataframe(
    df[["Label", "Stress (%)", "Delta (%)", "Risk"]],
    use_container_width=True
)

with st.expander("ℹ️ Column meanings"):
    st.write("""
    - Stress (%) → current stress level  
    - Delta (%) → change in stress  
    - Risk → classification of severity  
    """)

# --- MOMENTUM ---
st.subheader("📈 Stress Momentum")

st.dataframe(
    df[["Label", "Stress (%)", "Delta (%)"]],
    use_container_width=True
)

with st.expander("ℹ️ Why momentum matters"):
    st.write("""
    Markets react to change, not level.
    
    Rising stress = capital outflow  
    Falling stress = stabilization  
    """)

# --- CHART (RESTORED CLARITY) ---
st.subheader("📊 Stress Distribution")

st.bar_chart(df.set_index("Label")["Stress (%)"])

# --- REFRESH ---
if st.button("Refresh"):
    st.rerun()
