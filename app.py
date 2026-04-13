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

# --- HEADER ---
col1, col2 = st.columns(2)

with col1:
    st.metric("Global Contagion Index (GCI)", gci)
    with st.expander("ℹ️ What is GCI?"):
        st.write("""
        Measures global macro stress across countries.
        
        > 0.75 = Crisis  
        0.6–0.75 = Contagion  
        0.4–0.6 = Regional stress  
        < 0.4 = Stable  
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

# --- COLOR LABEL FUNCTION ---
def stress_label(val):
    if val > 0.75:
        return "🔴 Crisis"
    elif val > 0.6:
        return "🟠 High"
    elif val > 0.4:
        return "🟡 Moderate"
    else:
        return "🟢 Stable"

df["Risk"] = df["Stress"].apply(stress_label)

# --- TOP RISK ---
st.subheader("🚨 Highest Risk Countries")

top_risk = df.head(5)
st.dataframe(top_risk, use_container_width=True)

with st.expander("ℹ️ Why this matters"):
    st.write("""
    Highest stress = early signals of instability.
    
    Clusters → contagion  
    Spikes → crisis onset  
    """)

# --- FULL TABLE ---
st.subheader("🌍 Global Stress Table")

st.dataframe(df, use_container_width=True)

with st.expander("ℹ️ Risk Guide"):
    st.write("""
    🔴 Crisis → extreme stress  
    🟠 High → elevated risk  
    🟡 Moderate → watch  
    🟢 Stable → low risk  
    """)

# --- CHART ---
st.subheader("📊 Stress Distribution")

st.bar_chart(df.set_index("Country")["Stress"])

# --- REFRESH ---
if st.button("Refresh"):
    st.rerun()
