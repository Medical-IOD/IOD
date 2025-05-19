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

# MediHive scenario
medi = df.copy()
medi["ASP Profit (6m)"] = medi["ASP All Dispense"] - total_var_cost
medi["AWP Profit (6m)"] = medi["AWP All Dispense"] - total_var_cost
medi["MediHive Share AWP"] = medi["AWP Profit (6m)"] * (share_pct / 100)

# Non‑MediHive scenario
non = df.copy()
non["ASP Profit (6m)"] = non["ASP All Dispense"] - total_var_cost - staff_cost/len(non)
non["AWP Profit (6m)"] = non["AWP All Dispense"] - total_var_cost - staff_cost/len(non)

# -----------------------------------
# Display tables

# Profit filter toggle
st.sidebar.markdown("---")
show_profitable_only = st.sidebar.checkbox("Only include profitable drugs in totals", value=True)

# Apply filter
if show_profitable_only:
    filter_mask = (df["ASP All Dispense"] - total_var_cost > 0) | (df["AWP All Dispense"] - total_var_cost > 0)
    df = df[filter_mask].reset_index(drop=True)

# Recompute scenario tables on filtered data
medi = df.copy()
medi["ASP Profit (6m)"] = medi["ASP All Dispense"] - total_var_cost
medi["AWP Profit (6m)"] = medi["AWP All Dispense"] - total_var_cost
medi["MediHive Share AWP"] = medi["AWP Profit (6m)"] * (share_pct / 100)

non = df.copy()
non["ASP Profit (6m)"] = non["ASP All Dispense"] - total_var_cost - staff_cost/len(non)
non["AWP Profit (6m)"] = non["AWP All Dispense"] - total_var_cost - staff_cost/len(non)

# Toggle filter for profitable drugs
st.subheader("🔢 MediHive Scenario")
col1, col2 = st.columns([3, 1])
with col2:
    col_filter1, col_filter2 = st.columns([3, 1])
with col_filter2:
    filter_toggle = st.checkbox("Only show profitable drugs", value=True, key="profitable_toggle_main")

if filter_toggle:
    mask = (df["ASP All Dispense"] - total_var_cost > 0) | (df["AWP All Dispense"] - total_var_cost > 0)
    df = df[mask].reset_index(drop=True)

# Recompute filtered scenario tables
medi = df.copy()
medi["ASP Profit (6m)"] = medi["ASP All Dispense"] - total_var_cost
medi["AWP Profit (6m)"] = medi["AWP All Dispense"] - total_var_cost
medi["MediHive Share AWP"] = medi["AWP Profit (6m)"] * (share_pct / 100)

non = df.copy()
non["ASP Profit (6m)"] = non["ASP All Dispense"] - total_var_cost - staff_cost/len(non)
non["AWP Profit (6m)"] = non["AWP All Dispense"] - total_var_cost - staff_cost/len(non)

# Display editable scenario tables

# Setup column layout with toggle for profitability filter
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("🔢 MediHive Scenario")
with col2:
    filter_toggle = st.checkbox("Only show profitable drugs", value=True)

# Apply filter
if filter_toggle:
    mask = (df["ASP All Dispense"] - total_var_cost > 0) | (df["AWP All Dispense"] - total_var_cost > 0)
    df = df[mask].reset_index(drop=True)

# Recompute scenario tables
medi = df.copy()
medi["ASP Profit (6m)"] = medi["ASP All Dispense"] - total_var_cost
medi["AWP Profit (6m)"] = medi["AWP All Dispense"] - total_var_cost
medi["MediHive Share AWP"] = medi["AWP Profit (6m)"] * (share_pct / 100)

non = df.copy()
non["ASP Profit (6m)"] = non["ASP All Dispense"] - total_var_cost - staff_cost/len(non)
non["AWP Profit (6m)"] = non["AWP All Dispense"] - total_var_cost - staff_cost/len(non)

# Display both scenario tables

save_changes = st.button("🔖 Save All Changes")
reset_data = st.button("↺ Reset to Original Upload")

if save_changes:
    st.success("Changes saved successfully (note: implement actual saving logic).")

if reset_data:
    st.session_state.df_original = st.session_state.uploaded_df.copy()
    st.session_state.df_current = st.session_state.df_original.copy()
    st.success("Data reset to original upload.")

st.markdown("""
### 🔢 Finalized Tables
Use the toggle to filter for profitable drugs only. Tables are editable. Add rows as needed.
""")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("""
    <h1 style='text-align: center; background-color: #002b36; color: white; padding: 20px; border-radius: 8px;'>
        💊 MediHiveRx In-Office Dispensing Profitability Tool
    </h1>
""", unsafe_allow_html=True)
st.subheader("MediHive Scenario")
with col2:
    filter_toggle = st.checkbox("Only show profitable drugs", value=True, key="profitable_toggle")

if filter_toggle:
    mask = (df["ASP All Dispense"] - total_var_cost > 0) | (df["AWP All Dispense"] - total_var_cost > 0)
    df = df[mask].reset_index(drop=True)

medi = df.copy()
medi["ASP Profit (6m)"] = medi["ASP All Dispense"] - total_var_cost
medi["AWP Profit (6m)"] = medi["AWP All Dispense"] - total_var_cost
medi["MediHive Share AWP"] = medi["AWP Profit (6m)"] * (share_pct / 100)

non = df.copy()
non["ASP Profit (6m)"] = non["ASP All Dispense"] - total_var_cost - staff_cost / len(non)
non["AWP Profit (6m)"] = non["AWP All Dispense"] - total_var_cost - staff_cost / len(non)

col1.data_editor(medi, use_container_width=True, key="medi_editor_filtered" if filter_toggle else "medi_editor_all", num_rows="dynamic")
st.subheader("Non-MediHive Scenario")
st.data_editor(non, use_container_width=True, key="non_editor_filtered" if filter_toggle else "non_editor_all", num_rows="dynamic")

# Debug table for ASP profitability
st.subheader("🔢 ASP Profit Debug Table")
with st.expander("Show Per-Drug Profit Breakdown"):
    debug_df = pd.DataFrame({
        "Drug": df["Drug Name"],
        "Dose_MG": df["Dose_MG"],
        "Rx Count": df["Rx Count"],
        "ASP Profit/Loss (UOM)": df["ASP Profit/Loss"],
        "ASP per Rx": df["ASP per Rx"],
        "ASP All Dispense": df["ASP All Dispense"],
        "Total Var Cost": df["Rx Count"] * (courier_rate + misc_rate),
        "ASP Final Profit": df["ASP All Dispense"] - (df["Rx Count"] * (courier_rate + misc_rate))
    })
    show_profitable_only = st.checkbox("Show only profitable drugs", value=True)
    if show_profitable_only:
        debug_df = debug_df[debug_df["ASP Final Profit"] > 0]
    st.dataframe(debug_df, use_container_width=True)
# -----------------------------------
st.subheader("📊 MediHive Scenario")
st.dataframe(medi, use_container_width=True)

colA, colB = st.columns(2)
with colA:
    st.metric("ASP Revenue", f"${medi['ASP Revenue'].sum():,.2f}")
    st.metric("ASP Profit", f"${medi['ASP Profit (6m)'].sum():,.2f}")
with colB:
    st.metric("AWP Revenue", f"${medi['AWP Revenue'].sum():,.2f}")
    st.metric("AWP Profit", f"${medi['AWP Profit (6m)'].sum():,.2f}")

st.markdown(f"**MediHive Share (AWP):** ${medi['MediHive Share AWP'].sum():,.2f}")
net_awp = medi['AWP Profit (6m)'].sum() - medi['MediHive Share AWP'].sum()
st.markdown(f"**Total AWP Net:** ${net_awp:,.2f}")

# --- Non‑MediHive ---
st.subheader("📊 Non‑MediHive Scenario")
st.dataframe(non, use_container_width=True)

colC, colD = st.columns(2)
with colC:
    st.metric("ASP Revenue", f"${non['ASP Revenue'].sum():,.2f}")
    st.metric("ASP Profit", f"${non['ASP Profit (6m)'].sum():,.2f}")
with colD:
    st.metric("AWP Revenue", f"${non['AWP Revenue'].sum():,.2f}")
    st.metric("AWP Profit", f"${non['AWP Profit (6m)'].sum():,.2f}")

st.markdown(f"**Non‑MediHive Expenses:** ${staff_cost:,.2f}")
st.markdown(f"**Total AWP Net:** ${non['AWP Profit (6m)'].sum():,.2f}")

# -----------------------------------
# Hypothetical simulator
# -----------------------------------
st.subheader("🧶 Hypothetical Revenue & Profit Simulator")
with st.expander("Try custom targets"):
    tgt_rev = st.number_input("Target Revenue", 0.0, 1e8, 0.0, 1000.0)
    tgt_pr = st.number_input("Target Net Profit", 0.0, 1e8, 0.0, 1000.0)
    if tgt_rev > 0 and tgt_pr > 0:
        st.success(f"Required Margin: {tgt_pr/tgt_rev*100:.2f}%")

# -----------------------------------
# Explanation footer
# -----------------------------------
st.markdown("""
---
**Formula Highlights**  
• *Revenue* = COGS + Profit (ASP / AWP)  
• *Profit columns* load negative, zero, and positive values verbatim  
• *MediHive Share* = AWP Profit × % slider  
• *Non‑MediHive Expenses* = Pharmacist + Technician + EMR + PSAO (6‑month costs)
""")
