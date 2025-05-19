import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="MediHiveRx Profitability Tool", layout="wide")

# --- HEADER ---
st.markdown("""
<h1 style='text-align: center; background-color: #004466; padding: 20px; color: white; border-radius: 8px;'>
    💊 MediHiveRx In-Office Dispensing Profitability Tool
</h1>
""", unsafe_allow_html=True)

# --- FILE UPLOAD ---
st.sidebar.header("Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Choose Excel file", type=[".xlsx"])

# --- USER INPUTS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Global Settings")
show_only_profitable = st.sidebar.checkbox("Only Show Profitable Drugs", value=True)
courier_cost_per_rx = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0)
misc_cost_per_rx = st.sidebar.number_input("Misc Supply Cost per Rx", min_value=0.0, value=1.5)
medihive_share_pct = st.sidebar.slider("MediHiveRx Share %", min_value=0, max_value=100, value=20, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("Non-MediHive Labor Inputs")
pharm_rate = st.sidebar.number_input("Pharmacist Hourly Rate ($)", value=65.0)
pharm_count = st.sidebar.number_input("Pharmacists (FTE)", value=1.0)
tech_rate = st.sidebar.number_input("Technician Hourly Rate ($)", value=30.0)
tech_count = st.sidebar.number_input("Technicians (FTE)", value=1.0)
emr_cost = st.sidebar.number_input("EMR Monthly Fee ($)", value=500.0)
psao_fee = st.sidebar.number_input("PSAO Monthly Fee ($)", value=300.0)

# --- DATA PROCESSING ---
def prepare_data(df):
    df = df.copy()

    # Strip currency symbols and convert to signed numeric values
    dollar_cols = [
        "ASP Profit/Loss", "AWP Profit/Loss", "NDC Purchase Price",
        "Purchase Price Per Code UOM", "CMS Payment Limit Profit/Loss"
    ]
    for col in dollar_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[\$,]", "", regex=True).str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            st.warning(f"Missing required column: {col}. Filling with zeros.")
            df[col] = 0.0

    required_cols = ["Dose", "Rx Count", "Code UOM"]
    for col in required_cols:
        if col not in df.columns:
            st.warning(f"Missing required column: {col}. Filling with zeros.")
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Ensure no zero division
    safe_uom = df["Code UOM"].replace(0, np.nan).fillna(1)
    dose = df["Dose"].fillna(0)
    df["ASP per Rx"] = (dose / safe_uom) * df["ASP Profit/Loss"].fillna(0)
    df["AWP per Rx"] = (dose / safe_uom) * df["AWP Profit/Loss"].fillna(0)
    df["ASP All Dispense"] = df["ASP per Rx"] * df["Rx Count"]
    df["AWP All Dispense"] = df["AWP per Rx"] * df["Rx Count"]

    return df

# --- FILTER PROFITABLE ---
def filter_profitable(df):
    asp = pd.to_numeric(df["ASP Profit/Loss"], errors="coerce")
    awp = pd.to_numeric(df["AWP Profit/Loss"], errors="coerce")
    return df[(asp > 0) | (awp > 0)] if show_only_profitable else df

# --- MAIN ---
if uploaded_file:
    df_raw = pd.read_excel(uploaded_file, sheet_name="Drug-Profitability")
    df = prepare_data(df_raw)
    vol = df["Rx Count"].sum()

    courier_total = courier_cost_per_rx * vol
    misc_total = misc_cost_per_rx * vol

    pharm_total = pharm_rate * 40 * 4 * 6 * pharm_count
    tech_total = tech_rate * 40 * 4 * 6 * tech_count
    emr_total = emr_cost * 6
    psao_total = psao_fee * 6
    nonmedi_expense_total = pharm_total + tech_total + emr_total + psao_total

    df_medi = filter_profitable(df.copy())
    df_non = filter_profitable(df.copy())

    asp_total_medi = df_medi["ASP All Dispense"].sum()
    awp_total_medi = df_medi["AWP All Dispense"].sum()
    asp_profit_medi = asp_total_medi - (courier_total + misc_total)
    awp_profit_medi = awp_total_medi - (courier_total + misc_total)

    awp_share = awp_profit_medi * (medihive_share_pct / 100)
    awp_net = awp_profit_medi - awp_share

    asp_total_non = df_non["ASP All Dispense"].sum()
    awp_total_non = df_non["AWP All Dispense"].sum()
    asp_profit_non = asp_total_non - (courier_total + misc_total + nonmedi_expense_total)
    awp_profit_non = awp_total_non - (courier_total + misc_total + nonmedi_expense_total)

    st.markdown("### MediHiveRx Scenario")
    st.data_editor(df_medi, use_container_width=True, key="medi_table", num_rows="dynamic")

    st.markdown("### Financial Summary – MediHive")
    st.write(f"**ASP Revenue:** ${asp_total_medi:,.2f}")
    st.write(f"**ASP Profit:** ${asp_profit_medi:,.2f}")
    st.write(f"**AWP Revenue:** ${awp_total_medi:,.2f}")
    st.write(f"**AWP Profit:** ${awp_profit_medi:,.2f}")
    st.write(f"**MediHive Share (AWP):** ${awp_share:,.2f}")
    st.write(f"**Total AWP Net:** ${awp_net:,.2f}")

    st.markdown("---")
    st.markdown("### Non-MediHive Scenario")
    st.data_editor(df_non, use_container_width=True, key="nonmedi_table", num_rows="dynamic")

    st.markdown("### Financial Summary – Non-MediHive")
    st.write(f"**ASP Revenue:** ${asp_total_non:,.2f}")
    st.write(f"**ASP Profit:** ${asp_profit_non:,.2f}")
    st.write(f"**AWP Revenue:** ${awp_total_non:,.2f}")
    st.write(f"**AWP Profit:** ${awp_profit_non:,.2f}")
    st.write(f"**Non-MediHive Expenses:** ${nonmedi_expense_total:,.2f}")
    st.write(f"**Total AWP Net:** ${awp_profit_non:,.2f}")

    st.markdown("---")
    st.markdown("### Hypothetical Target Calculator")
    col1, col2 = st.columns(2)
    with col1:
        target_rev = st.number_input("Target Revenue ($)", value=500000.0)
    with col2:
        target_margin_pct = st.slider("Target Profit Margin %", min_value=0.0, max_value=100.0, value=5.0)

    target_profit = target_rev * (target_margin_pct / 100)
    st.success(f"**Target Profit = ${target_profit:,.2f}** from ${target_rev:,.2f} in Revenue at {target_margin_pct:.1f}% margin")
else:
    st.info("Please upload a data file to begin.")
