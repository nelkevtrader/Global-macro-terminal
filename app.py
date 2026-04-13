import streamlit as st
import requests
import pandas as pd
import numpy as np

API = "https://global-macro-terminal-1.onrender.com/global-state"

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

# --- CURRENCY → COUNTRY MAP ---
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
data = requests.get(API).json()

countries = data["countries"]
gci = data["GCI"]
regime = data["regime"]

df = pd.DataFrame(list(countries.items()), columns=["Currency", "Stress"])

# --- LABELING ---
df["Country"] = df["Currency"].map(currency_map)
df["Label"] = df["Currency"] + " - " + df["Country"].fillna("Unknown")

df = df.sort_values(by="Stress", ascending=False)

# --- SIMULATE PREVIOUS DATA ---
df["Prev_Stress"] = df["Stress"] + np.random.normal(0, 0.05, len(df))
df["Delta"] = df["Stress"] - df["Prev_Stress"]

# --- CONVERT TO % ---
df["Stress (%)"] = (df["Stress"] * 100).round(1)
df["Delta (%)"] = (df["Delta"] * 100).round(1)

# --- HEADER ---
col1, col2 = st.columns(2)

with col1:
    st.metric("Global Contagion Index (GCI)", f"{round(gci*100,1)}%")
    with st.expander("ℹ️ What is GCI?"):
        st.write("""
        Measures global macro stress across countries.
        
        > 75% = Crisis  
        60–75% = Contagion  
        40–60% = Regional stress  
        < 40% = Stable  
        """)

with col2:
    st.metric("Regime", regime)
    with st.expander("ℹ️ What does this mean?"):
        st.write("""
        - Stable → calm conditions  
        - Regional Stress → localized issues  
        - Contagion → spreading instability  
        - Crisis → systemic risk  
        """)

st.divider()

# --- RISK LABEL ---
def stress_label(val):
    if val > 75:
        return "🔴 Crisis"
    elif val > 60:
        return "🟠 High"
    elif val > 40:
        return "🟡 Moderate"
    else:
        return "🟢 Stable"

df["Risk"] = df["Stress (%)"].apply(stress_label)

# --- ALERT SYSTEM ---
alerts = df[df["Delta (%)"] > 15]

if not alerts.empty:
    st.error("🚨 ALERT: Rapid Stress Increase Detected")
    st.dataframe(alerts[["Label", "Delta (%)"]], use_container_width=True)

# --- TOP RISK ---
st.subheader("🚨 Highest Risk Countries")

top_risk = df.head(5)
st.dataframe(
    top_risk[["Label", "Stress (%)", "Risk"]],
    use_container_width=True
)

with st.expander("ℹ️ Why this matters"):
    st.write("""
    Highest stress = early signals of instability.
    
    Clusters → contagion  
    Spikes → crisis onset  
    """)

# --- FULL TABLE ---
st.subheader("🌍 Global Stress Table")

st.dataframe(
    df[["Label", "Stress (%)", "Delta (%)", "Risk"]],
    use_container_width=True
)

with st.expander("ℹ️ Risk Guide"):
    st.write("""
    🔴 Crisis → extreme stress  
    🟠 High → elevated risk  
    🟟 Moderate → watch  
    🟢 Stable → low risk  
    """)

# --- MOMENTUM ---
st.subheader("📈 Stress Momentum")

st.dataframe(
    df[["Label", "Stress (%)", "Delta (%)"]],
    use_container_width=True
)

with st.expander("ℹ️ Why momentum matters"):
    st.write("""
    Markets react to change, not levels.
    
    Rising stress = capital leaving  
    Falling stress = stabilization  
    
    Large increases = early warning signal  
    """)

# --- CHART ---
st.subheader("📊 Stress Distribution")

chart_df = df.set_index("Label")["Stress (%)"]
st.bar_chart(chart_df)

# --- REFRESH ---
if st.button("Refresh"):
    st.rerun()
