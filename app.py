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

col1, col2 = st.columns(2)

with col1:
    st.metric("Global Contagion Index (GCI)", gci)

with col2:
    st.metric("Regime", regime)

st.divider()

st.subheader("Country Stress Levels")
st.dataframe(df, use_container_width=True)

st.subheader("Stress Distribution")
st.bar_chart(df.set_index("Country"))

if st.button("Refresh"):
    st.rerun()
