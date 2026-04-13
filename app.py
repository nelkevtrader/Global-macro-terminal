import streamlit as st
import requests
import pandas as pd

API = "https://global-macro-terminal-1.onrender.com/global-state"

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

# --- LOAD DATA ---
data = requests.get(API).json()

countries = data["countries"]
gci = data["GCI"]
regime = data["regime"]

df = pd.DataFrame(list(countries.items()), columns=["Country", "Stress"])
df = df.sort_values(by="Stress", ascending=False)

# --- HEADER METRICS ---
col1, col2 = st.columns(2)

with col1:
    st.metric("Global Contagion Index (GCI)", gci)
    with st.expander("ℹ️ What is GCI?"):
        st.write("""
        The Global Contagion Index measures average stress across all countries.
        
        > 0.75 = Crisis  
        0.6–0.75 = Contagion  
        0.4–0.6 = Regional stress  
        < 0.4 = Stable  
        """)

with col2:
    st.metric("Regime", regime)
    with st.expander("ℹ️ What does this mean?"):
        st.write("""
        - Stable → low volatility  
        - Regional Stress → localized issues  
        - Contagion Stress → spreading instability  
        - Crisis → global systemic risk  
        """)

st.divider()

# --- COLOR FUNCTION ---
def color_stress(val):
    if val > 0.75:
        return 'background-color: red; color: white'
    elif val > 0.6:
        return 'background-color: orange'
    elif val > 0.4:
        return 'background-color: yellow'
    else:
        return 'background-color: green; color: white'

styled_df = df.style.applymap(color_stress, subset=["Stress"])

# --- TOP RISK COUNTRIES ---
st.subheader("🚨 Highest Risk Countries")

top_risk = df.head(5)
st.dataframe(top_risk, use_container_width=True)

with st.expander("ℹ️ Why this matters"):
    st.write("""
    These are the countries under the highest stress right now.
    
    Watch for:
    - clusters → contagion risk  
    - sudden spikes → early crisis signal  
    """)

# --- FULL HEATMAP TABLE ---
st.subheader("🌍 Global Stress Heatmap")

st.dataframe(styled_df, use_container_width=True)

with st.expander("ℹ️ Color Guide"):
    st.write("""
    🔴 Red → Crisis  
    🟠 Orange → High stress  
    🟡 Yellow → Moderate  
    🟢 Green → Stable  
    """)

# --- CHART ---
st.subheader("📊 Stress Distribution")

st.bar_chart(df.set_index("Country"))

# --- REFRESH BUTTON ---
if st.button("Refresh"):
    st.rerun()
