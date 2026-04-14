import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(layout="wide")
st.title("🌍 Macro Quant Model v2 — Regime + Contagion Engine")

# =========================================================
# CORE UNIVERSE (DETERMINISTIC BASE)
# =========================================================
BASE = {
    "EGP": 0.82, "TRY": 0.80, "ARS": 0.88,
    "NGN": 0.76, "ZAR": 0.56, "PKR": 0.78,
    "LKR": 0.72, "GHS": 0.64, "KES": 0.61,
    "USD": 0.30, "EUR": 0.36, "JPY": 0.42,
    "GBP": 0.39, "CNY": 0.46, "INR": 0.53,
    "BRL": 0.59, "MXN": 0.51, "RUB": 0.79,
    "IDR": 0.50, "VND": 0.48
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
# STRUCTURAL MACRO DRIVERS (NEW IN V2)
# =========================================================

# Inflation pressure proxy (deterministic structural bias)
INFLATION_BIAS = {
    "EGP": 1.25, "TRY": 1.30, "ARS": 1.35,
    "NGN": 1.20, "ZAR": 1.05, "PKR": 1.18,
    "LKR": 1.15, "GHS": 1.10, "KES": 1.08,
    "USD": 0.95, "EUR": 0.96, "JPY": 0.97,
    "GBP": 0.94, "CNY": 0.98, "INR": 1.00,
    "BRL": 1.06, "MXN": 1.02, "RUB": 1.28,
    "IDR": 0.99, "VND": 0.98
}

# Liquidity stress (global dollar sensitivity)
LIQUIDITY_BIAS = {
    "EGP": 1.20, "TRY": 1.18, "ARS": 1.25,
    "NGN": 1.15, "ZAR": 1.05, "PKR": 1.14,
    "LKR": 1.12, "GHS": 1.08, "KES": 1.06,
    "USD": 0.85, "EUR": 0.90, "JPY": 0.88,
    "GBP": 0.89, "CNY": 0.92, "INR": 0.98,
    "BRL": 1.03, "MXN": 1.00, "RUB": 1.22,
    "IDR": 0.97, "VND": 0.96
}

# FX vulnerability (structural)
FX_BIAS = {
    "EGP": 1.25, "TRY": 1.22, "ARS": 1.30,
    "NGN": 1.18, "ZAR": 1.05, "PKR": 1.17,
    "LKR": 1.12, "GHS": 1.10, "KES": 1.07,
    "USD": 0.90, "EUR": 0.92, "JPY": 0.93,
    "GBP": 0.91, "CNY": 0.95, "INR": 1.00,
    "BRL": 1.04, "MXN": 1.01, "RUB": 1.24,
    "IDR": 0.98, "VND": 0.97
}

# =========================================================
# MULTI-FACTOR STRESS ENGINE
# =========================================================
def stress(ccy):
    base = BASE[ccy]
    inf = INFLATION_BIAS[ccy]
    liq = LIQUIDITY_BIAS[ccy]
    fx = FX_BIAS[ccy]

    # weighted macro model (deterministic)
    return base * (0.4*inf + 0.35*liq + 0.25*fx)

rows = []
for ccy in BASE:
    s = stress(ccy)
    rows.append([ccy, NAME.get(ccy, ccy), s])

df = pd.DataFrame(rows, columns=["Currency", "Country", "Stress"])

# =========================================================
# NORMALIZATION (IMPORTANT FIX)
# =========================================================
df["Stress Score"] = (df["Stress"] * 100).round(2)

df = df.sort_values("Stress Score", ascending=False).reset_index(drop=True)

# deterministic delta (rank-based)
df["Delta"] = df["Stress Score"].diff().fillna(0).round(2)

# =========================================================
# SIGNAL ENGINE (MULTI-LAYER)
# =========================================================
df["Signal"] = (
    df["Stress Score"] * 0.55 +
    df["Delta"].abs() * 0.25 +
    (df["Stress Score"].rolling(3).mean().fillna(df["Stress Score"])) * 0.20
)

df["Signal"] = df["Signal"].clip(0, 100).round(2)

# =========================================================
# CONTAGION ENGINE (NEW IN V2)
# =========================================================
global_pressure = df["Stress Score"].mean()

df["Contagion"] = (df["Stress Score"] - global_pressure).abs().round(2)

# =========================================================
# REGIME ENGINE (NEW IN V2)
# =========================================================
def regime(x):
    if x > 75:
        return "🔴 Crisis Regime"
    elif x > 60:
        return "🟠 Stress Regime"
    elif x > 45:
        return "🟡 Transition"
    return "🟢 Stable"

df["Regime"] = df["Signal"].apply(regime)

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
# MACRO RISK INDEX (CMRI v2)
# =========================================================
cmri = df["Signal"].mean().round(2)

if cmri > 70:
    macro_regime = "🔴 Global Risk-Off"
elif cmri > 55:
    macro_regime = "🟠 Elevated Risk"
elif cmri > 40:
    macro_regime = "🟡 Neutral"
else:
    macro_regime = "🟢 Risk-On"

# =========================================================
# HEADER
# =========================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("CMRI v2", cmri)

with c2:
    st.metric("BTC", f"${btc:,.0f}" if btc else "N/A")

with c3:
    st.metric("Gold", f"${gold:,.0f}" if gold else "N/A")

with c4:
    st.metric("Macro Regime", macro_regime)

st.divider()

# =========================================================
# TOP RISKS
# =========================================================
st.subheader("🚨 Systemic Risk Leaders")

st.dataframe(
    df.head(7)[["Currency","Country","Stress Score","Signal","Regime","Contagion"]],
    use_container_width=True
)

# =========================================================
# FULL MODEL
# =========================================================
st.subheader("🌍 Macro Quant Map v2")

st.dataframe(
    df[["Currency","Country","Stress Score","Delta","Signal","Regime","Contagion"]],
    use_container_width=True
)

# =========================================================
# STABLE CHART
# =========================================================
st.subheader("📊 Systemic Stress Distribution")

st.bar_chart(df.set_index("Country")["Signal"])

# =========================================================
# FOOTER INSIGHT
# =========================================================
st.caption(
    "v2 adds inflation + liquidity + FX structural stress + contagion + regime transitions. Fully deterministic model."
)
