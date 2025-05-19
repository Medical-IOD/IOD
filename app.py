import streamlit as st
import pandas as pd
import numpy as np

FTE_HOURS_6M = 40 * 52 / 2  # 1040 hours

st.set_page_config(page_title="MediHive In‑Office Dispensing Pro Forma", layout="wide")

# --- CSS: green slider thumb ---
st.markdown("""
<style>
input[type=range]::-webkit-slider-thumb{background:#2ecc71!important}
input[type=range]::-moz-range-thumb{background:#2ecc71!important}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# Helper: robust money → float (keeps negatives)
# -----------------------------------
def money_to_float(col: pd.Series):
    return pd.to_numeric(
        col.astype(str)
        .str.replace(r"[,$]", "", regex=True)
        .str.replace(r"\((.+)\)", r"-\1", regex=True),
        errors="coerce")

# -----------------------------------
# Upload Excel
# -----------------------------------
uploaded_file = st.sidebar.file_uploader("Upload Profitability Excel", type=["xlsx"])
if not uploaded_file:
    st.info("Upload the Excel file to begin.")
    st.stop()

# -----------------------------------
# Load & clean
# -----------------------------------
df = pd.read_excel(uploaded_file, sheet_name="Drug-Profitability")

df["NDC"] = df["NDC"].astype(str).str.replace("-", "").str.strip()

df["Dose_MG"] = (
    df["Strength"].astype(str)
    .str.extract(r"([\d,.]+)")[0]
    .str.replace(",", "")
    .astype(float))

df["Rx Count"] = pd.to_numeric(df["Rx Count"], errors="coerce").fillna(0)

df["Purchase Price Per Code UOM"] = money_to_float(df["Purchase Price Per Code UOM"]).fillna(0)

df["ASP Profit/Loss"] = money_to_float(df["ASP Profit/Loss"]).fillna(0)

df["AWP Profit/Loss"] = money_to_float(df["AWP Profit/Loss"]).fillna(0)

# -----------------------------------
# Core calcs
# -----------------------------------
df["ASP per Rx"] = df["Dose_MG"] * df["ASP Profit/Loss"]
df["AWP per Rx"] = df["Dose_MG"] * df["AWP Profit/Loss"]
df["ASP All Dispense"] = df["ASP per Rx"] * df["Rx Count"]
df["AWP All Dispense"] = df["AWP per Rx"] * df["Rx Count"]

df["Total COGS"] = df["Purchase Price Per Code UOM"] * df["Dose_MG"] * df["Rx Count"]

df["ASP Revenue"] = df["Total COGS"] + df["ASP All Dispense"]
df["AWP Revenue"] = df["Total COGS"] + df["AWP All Dispense"]

# -----------------------------------
# Sidebar parameters
# -----------------------------------
st.sidebar.header("Variable Costs & Share")
courier_rate = st.sidebar.number_input("Courier Cost / Rx", 0.0, 100.0, 8.0, 0.5)
misc_rate = st.sidebar.number_input("Misc Supply Cost / Rx", 0.0, 100.0, 2.0, 0.5)
share_pct = st.sidebar.slider("MediHiveRx % Share", 0.0, 100.0, 20.0, 1.0)

st.sidebar.header("Non‑MediHive Staffing")
ph_cnt = st.sidebar.number_input("Pharmacist Headcount", 0, 10, 1)
ph_rate = st.sidebar.number_input("Pharmacist $/hr", 0.0, 300.0, 60.0)
tech_cnt = st.sidebar.number_input("Technician Headcount", 0, 10, 1)
tech_rate = st.sidebar.number_input("Technician $/hr", 0.0, 150.0, 25.0)
emr_cost = st.sidebar.number_input("EMR (6m)", 0.0, 1e5, 3000.0, 100.0)
psao_cost = st.sidebar.number_input("PSAO (6m)", 0.0, 1e5, 2500.0, 100.0)

staff_cost = (ph_cnt*ph_rate + tech_cnt*tech_rate) * FTE_HOURS_6M + emr_cost + psao_cost

# -----------------------------------
# Variable costs (applied to total Rx Count)
total_rxs = df['Rx Count'].sum()
total_courier = total_rxs * courier_rate
total_misc = total_rxs * misc_rate
total_var_cost = total_courier + total_misc

# MediHive scenario table
medi = df.copy()
medi["ASP Profit (6m)"] = medi["ASP All Dispense"] - total_var_cost
medi["AWP Profit (6m)"] = medi["AWP All Dispense"] - total_var_cost
medi["MediHive Share AWP"] = medi["AWP Profit (6m)"] * (share_pct / 100)
