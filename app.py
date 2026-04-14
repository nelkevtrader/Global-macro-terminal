import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(layout="wide")
st.title("🌍 Macro Quant Model v1 — Deterministic Engine")

# =========================================================
# BASE STRUCTURE (NO RANDOMNESS)
# =========================================================
BASE = {
    "EGP": 0.80, "TRY": 0.78, "ARS": 0.85,
    "NGN": 0.74, "ZAR": 0.55, "PKR": 0.76,
    "LKR": 0.70, "GHS": 0.62, "KES": 0.60,
    "USD": 0.30, "EUR": 0.35, "JPY": 0.40,
    "GBP": 0.38, "CNY": 0.45, "INR": 0.52,
    "BRL": 0.58, "MXN": 0.50, "RUB": 0.77,
    "IDR": 0.49, "VND": 0.47
}

NAME = {
    "EGP": "Egypt","TRY": "Turkey","ARS": "Argentina",
    "NGN": "Nigeria","ZAR": "South Africa","PKR": "Pakistan",
    "LKR": "Sri Lanka","GHS": "Ghana","KES": "Kenya",
    "USD": "United States","EUR": "Eurozone","JPY": "Japan",
    "GBP": "United Kingdom","CNY": "China","INR": "India",
    "BRL": "Brazil","MXN": "Mexico","RUB": "Russia",
    "IDR": "Indonesia","VND": "Vietnam"
}

# =========================================================
# FX STRESS FACTOR (STABLE MODEL)
# =========================================================
FX_IMPACT = {
    "EGP": 1.20, "TRY": 1.18, "ARS": 1.25,
    "NGN": 1.15, "ZAR": 1.05, "PKR": 1.14,
    "LKR": 1.10, "GHS": 1.08, "KES": 1.06,
    "USD": 0.90, "EUR": 0.92, "JPY": 0.93,
    "GBP": 0.91, "CNY": 0.95, "INR": 1.00,
    "BRL": 1.03, "MXN": 0.99, "RUB": 1.17,
    "IDR": 0.97, "VND": 0.96
}

# =========================================================
# STRESS ENGINE (CORE MODEL)
# =========================================================
def stress_model(base, ccy):
    fx = FX_IMPACT.get(ccy, 1.0)
    return base * fx

rows = []
for ccy, base in BASE.items():
    s = stress_model(base, ccy)
    rows.append([ccy, NAME.get(ccy, ccy), s])

df = pd.DataFrame(rows, columns=["Currency", "Country", "Stress"])

# Normalize (quant-style scaling)
df["Stress Score"] = (df["Stress"] * 100).round(2)

# Rank system (IMPORTANT FIX FOR STABILITY)
df = df.sort_values("Stress Score", ascending=False).reset_index(drop=True)

# Delta is deterministic (rank-based)
df["Delta"] = df["Stress Score"].diff().fillna(0).round(2)

# =========================================================
# SIGNAL MODEL (MULTI-FACTOR QUANT STYLE)
# =========================================================
df["Signal"] = (
    df["Stress Score"] * 0.6 +
    df["Delta"].abs() * 0.4
)

df["Signal"] = df["Signal"].clip(0, 100).round(2)

# =========================================================
# RISK REGIME CLASSIFICATION
# =========================================================
def risk(x):
    if x > 75:
        return "🔴 Risk-Off Extreme"
    elif x > 60:
        return "🟠 Risk-Off"
    elif x > 40:
        return "🟡 Neutral"
    return "🟢 Risk-On"

df["Regime"] = df["Signal"].apply(risk)

# =========================================================
# CROSS-ASSET ANCHORS
# =========================================================
def get_btc():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=6
        )
        return r.json()["bitcoin"]["usd"]
    except:
        return None

def get_gold():
    try:
        r = requests.get("https://stooq.com/q/l/?s=xauusd&i=d", timeout=6)
        return float(r.text.split("\n")[1].split(",")[3])
    except:
        return None

btc = get_btc()
gold = get_gold()

# =========================================================
# GLOBAL MACRO RISK INDEX (CMRI)
# =========================================================
cmri = df["Signal"].mean().round(2)

if cmri > 70:
    regime = "🔴 Global Risk-Off"
elif cmri > 50:
    regime = "🟠 Elevated Risk"
else:
    regime = "🟢 Stable Macro Regime"

# =========================================================
# HEADER
# =========================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("CMRI", cmri)

with c2:
    st.metric("BTC", f"${btc:,.0f}" if btc else "N/A")

with c3:
    st.metric("Gold", f"${gold:,.0f}" if gold else "N/A")

with c4:
    st.metric("Regime", regime)

st.divider()

# =========================================================
# TOP RISKS
# =========================================================
st.subheader("🚨 Macro Risk Leaders")

st.dataframe(
    df.head(7)[["Currency","Country","Stress Score","Signal","Regime"]],
    use_container_width=True
)

# =========================================================
# FULL MODEL
# =========================================================
st.subheader("🌍 Macro Quant Map")

st.dataframe(
    df[["Currency","Country","Stress Score","Delta","Signal","Regime"]],
    use_container_width=True
)

# =========================================================
# STABLE CHART
# =========================================================
st.subheader("📊 Risk Distribution")

st.bar_chart(df.set_index("Country")["Signal"])

# =========================================================
# EXPLANATION
# =========================================================
st.caption(
    "Macro Quant Model v1: deterministic factor-based stress model with regime classification and cross-asset anchors."
)
