import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

# ----------------------------
# DATA SOURCE
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
# LOAD DATA
# ----------------------------
data = requests.get(API).json()

df = pd.DataFrame(list(data["countries"].items()), columns=["Currency", "Stress"])

df["Country"] = df["Currency"].map(currency_map).fillna(df["Currency"])
df["Label"] = df["Currency"] + " - " + df["Country"]

df = df.sort_values(by="Stress", ascending=False)

# ----------------------------
# SIMULATED MOMENTUM (Δ)
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
def risk_label(x):
    if x > 75:
        return "🔴 Crisis"
    elif x > 60:
        return "🟠 High"
    elif x > 40:
        return "🟡 Moderate"
    return "🟢 Stable"

df["Risk"] = df["Stress (%)"].apply(risk_label)

# ----------------------------
# HEADER METRICS
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    st.metric("Global Contagion Index", f"{round(data['GCI']*100,1)}%")
    with st.expander("ℹ️ What is this?"):
        st.write("""
        A synthetic macro stress indicator combining global risk conditions.
        
        Higher values = higher systemic instability.
        """)

with col2:
    st.metric("Regime", data["regime"])
    with st.expander("ℹ️ Regime meaning"):
        st.write("""
        - Stable → low volatility  
        - Regional Stress → localized issues  
        - Contagion → spreading instability  
        - Crisis → systemic breakdown risk  
        """)

st.divider()

# ----------------------------
# ALERT SYSTEM
# ----------------------------
alerts = df[df["Delta (%)"] > 15]

if not alerts.empty:
    st.error("🚨 ALERT: Rapid Stress Increase Detected")
    st.dataframe(alerts[["Label", "Delta (%)"]], use_container_width=True)

# ----------------------------
# TOP RISK
# ----------------------------
st.subheader("🚨 Highest Risk Countries")

top = df.head(5)

st.dataframe(
    top[["Label", "Stress (%)", "Risk"]],
    use_container_width=True
)

with st.expander("ℹ️ Why this matters"):
    st.write("""
    High stress clusters often precede:
    - currency depreciation  
    - capital flight  
    - policy intervention  
    """)

# ----------------------------
# FULL TABLE
# ----------------------------
st.subheader("🌍 Global Stress Table")

display_df = df[["Label", "Stress (%)", "Delta (%)", "Risk"]]

st.dataframe(display_df, use_container_width=True)

with st.expander("ℹ️ Column guide"):
    st.write("""
    - Stress (%) → current stress level  
    - Delta (%) → change in stress  
    - Risk → severity classification  
    """)

# ----------------------------
# MOMENTUM VIEW
# ----------------------------
st.subheader("📈 Stress Momentum")

st.dataframe(
    df[["Label", "Stress (%)", "Delta (%)"]],
    use_container_width=True
)

with st.expander("ℹ️ Why momentum matters"):
    st.write("""
    Markets react to change, not static levels.
    
    Rising stress = worsening conditions  
    Falling stress = stabilization  
    """)

# ----------------------------
# CHART
# ----------------------------
st.subheader("📊 Stress Distribution")

st.bar_chart(df.set_index("Label")["Stress (%)"])

# ----------------------------
# REFRESH
# ----------------------------
if st.button("Refresh"):
    st.rerun()
