import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(layout="wide")
st.title("🌍 Global Macro Stress Terminal — Deterministic Engine")

# =========================================================
# FIXED INPUT DATA (NO EXTERNAL RANDOM BACKEND)
# =========================================================

BASE_COUNTRIES = {
    "EGP": 0.78, "TRY": 0.72, "ARS": 0.85,
    "NGN": 0.70, "ZAR": 0.55, "PKR": 0.73,
    "LKR": 0.68, "GHS": 0.60, "KES": 0.57,
    "USD": 0.30, "EUR": 0.35, "JPY": 0.40,
    "GBP": 0.38, "CNY": 0.45, "INR": 0.52,
    "BRL": 0.58, "MXN": 0.50, "RUB": 0.75,
    "IDR": 0.49, "VND": 0.47
}

currency_map = {
    "EGP": "Egypt","TRY": "Turkey","ARS": "Argentina",
    "NGN": "Nigeria","ZAR": "South Africa","PKR": "Pakistan",
    "LKR": "Sri Lanka","GHS": "Ghana","KES": "Kenya",
    "USD": "United States","EUR": "Eurozone","JPY": "Japan",
    "GBP": "United Kingdom","CNY": "China","INR": "India",
    "BRL": "Brazil","MXN": "Mexico","RUB": "Russia",
    "IDR": "Indonesia","VND": "Vietnam"
}

# =========================================================
# DETERMINISTIC ENGINE (NO RANDOMNESS)
# =========================================================
def compute_stress(base_value, currency):
    """
    Deterministic adjustment based on FX sensitivity proxy
    """
    fx_factor = {
        "EGP": 1.15, "TRY": 1.12, "ARS": 1.18,
        "NGN": 1.10, "ZAR": 1.05, "PKR": 1.11,
        "LKR": 1.09, "GHS": 1.06, "KES": 1.04,
        "USD": 0.90, "EUR": 0.92, "JPY": 0.93,
        "GBP": 0.91, "CNY": 0.95, "INR": 1.00,
        "BRL": 1.03, "MXN": 0.99, "RUB": 1.14,
        "IDR": 0.97, "VND": 0.96
    }

    return round(base_value * fx_factor.get(currency, 1.0), 4)

# =========================================================
# BUILD DATAFRAME (DETERMINISTIC ONLY)
# =========================================================
rows = []
for ccy, base in BASE_COUNTRIES.items():
    stress = compute_stress(base, ccy)
    rows.append([ccy, currency_map.get(ccy, ccy), stress])

df = pd.DataFrame(rows, columns=["Currency", "Country", "Stress"])

df["Label"] = df["Currency"] + " - " + df["Country"]

# FIXED (NO RANDOM DRIFT)
df["Stress (%)"] = (df["Stress"] * 100).round(2)

# Deterministic delta (stable ordering only)
df = df.sort_values("Stress (%)", ascending=False)
df["Delta (%)"] = df["Stress (%)"].diff().fillna(0).round(2)

# =========================================================
# SIGNAL MODEL (STABLE)
# =========================================================
df["Signal (%)"] = (
    df["Stress (%)"] * 0.7 +
    df["Delta (%)"].abs() * 0.3
)

df["Signal (%)"] = df["Signal (%)"].clip(0, 100).round(2)

# =========================================================
# RISK LABELS
# =========================================================
def risk(x):
    if x > 75:
        return "🔴 High Risk"
    elif x > 60:
        return "🟠 Warning"
    elif x > 40:
        return "🟡 Elevated"
    return "🟢 Stable"

df["Risk"] = df["Signal (%)"].apply(risk)

# =========================================================
# SAFE MARKET DATA (NO RELIANCE ON UNSTABLE BACKENDS)
# =========================================================
def safe_price(url, key=None):
    try:
        r = requests.get(url, timeout=6)
        data = r.json()
        if key:
            return data[key]
        return data
    except:
        return None

# BTC
btc = None
try:
    btc = safe_price("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")["bitcoin"]["usd"]
except:
    btc = None

# GOLD (ONLY ONE SOURCE — STABLE + NO N/A CHAINS)
gold = None
try:
    r = requests.get("https://stooq.com/q/l/?s=xauusd&i=d", timeout=6)
    line = r.text.split("\n")[1].split(",")
    gold = float(line[3])
except:
    gold = None

# =========================================================
# HEADER
# =========================================================
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Bitcoin", f"${btc:,.0f}" if btc else "N/A")

with c2:
    st.metric("Gold", f"${gold:,.0f}" if gold else "N/A")

with c3:
    st.metric("Countries Tracked", len(df))

st.divider()

# =========================================================
# TOP RISK
# =========================================================
st.subheader("🚨 Highest Risk Countries (Stable)")

st.dataframe(
    df.sort_values("Signal (%)", ascending=False)
    [["Label","Stress (%)","Signal (%)","Risk"]]
    .head(7),
    use_container_width=True
)

# =========================================================
# FULL TABLE
# =========================================================
st.subheader("🌍 Macro Stress Map (Deterministic)")

st.dataframe(
    df[["Label","Stress (%)","Delta (%)","Signal (%)","Risk"]],
    use_container_width=True
)

# =========================================================
# STABLE CHART (THIS WILL NO LONGER BREAK)
# =========================================================
st.subheader("📊 Signal Distribution")

chart_df = df.set_index("Label")["Signal (%)"]
st.bar_chart(chart_df)

# =========================================================
# EXPLANATION
# =========================================================
st.caption(
    "This system is fully deterministic. No external macro backend. "
    "All values are reproducible and stable per session."
)
