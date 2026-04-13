import streamlit as st
import requests
import pandas as pd

API = "https://global-macro-terminal-1.onrender.com/global-state"

st.set_page_config(layout="wide")

st.title("🌍 Global Macro Stress Terminal")

data = requests.get(API).json()

countries = data["countries"]
gci = data["GCI"]
regime = data["regime"]

df = pd.DataFrame(list(countries.items()), columns=["Country", "Stress"])
df = df.sort_values(by="Stress", ascending=False)

# --- HEADER METRICS WITH INFO ---
col1, col2 = st.columns(2)

with col1:
    st.metric("Global Contagion Index (GCI)", gci)
    with st.expander("ℹ️ What is GCI?"):
        st.write("""
        The Global Contagion Index measures the average stress across all tracked countries.
        
        Higher values indicate:
        - capital flight
        - currency instability
        - rising systemic risk
        
        > 0.75 = Crisis conditions  
        0.6–0.75 = Contagion spreading  
        0.4–0.6 = Regional stress  
        < 0.4 = Stable
        """)

with col2:
    st.metric("Regime", regime)
    with st.expander("ℹ️ What does this mean?"):
        st.write("""
        The regime indicates the current macro environment:
        
        - **Stable** → low volatility  
        - **Regional Stress** → localized issues  
        - **Contagion Stress** → spreading instability  
        - **Crisis** → systemic global risk
        """)

st.divider()

# --- COUNTRY TABLE ---
st.subheader("Country Stress Levels")

with st.expander("ℹ️ How to read this table"):
    st.write("""
    Each country has a stress score between 0 and 1.
    
    Higher = more pressure on:
    - currency
    - capital flows
    - economic stability
    
    Watch for:
    - clusters of high values
    - rapid increases
    """)

st.dataframe(df, use_container_width=True)

# --- BAR CHART ---
st.subheader("Stress Distribution")

with st.expander("ℹ️ Chart explanation"):
    st.write("""
    This chart shows relative stress levels across countries.
    
    Key signals:
    - multiple high bars → contagion risk
    - one extreme bar → localized crisis
    """)

st.bar_chart(df.set_index("Country"))

# --- REFRESH ---
if st.button("Refresh"):
    st.rerun()
