import streamlit as st
import pandas as pd
import numpy as np

# Constants for FTE calculation
FTE_HOURS_6M = 40 * 52 / 2  # 1040 hours in 6 months per FTE

st.set_page_config(page_title="MediHive In-Office Dispensing Pro Forma", layout="wide")

# Style slider thumb green
st.markdown("""
<style>
input[type=range]::-webkit-slider-thumb { background: #2ecc71 !important; }
input[type=range]::-moz-range-thumb { background: #2ecc71 !important; }
</style>
""", unsafe_allow_html=True)

# File upload
uploaded_file = st.sidebar.file_uploader("Upload Profitability Excel", type=["xlsx"])
if not uploaded_file:
    st.info("Please upload the profitability Excel file to proceed.")
else:
    # Load data
    df = pd.read_excel(uploaded_file, sheet_name="Drug-Profitability")
    # Clean and convert columns
    df["NDC"] = df["NDC"].astype(str).str.replace("-", "").str.strip()
    df["Dose_MG"] = (
        df["Strength"].astype(str)
        .str.extract(r"([\d,.]+)")[0]
        .str.replace(",", "")
        .astype(float)
    )
    df["Rx Count"] = pd.to_numeric(df["Rx Count"], errors="coerce").fillna(0)
    df["Purchase Price Per Code UOM"] = pd.to_numeric(
        df["Purchase Price Per Code UOM"]
        .astype(str)
        .str.replace(r"[$,]", "", regex=True),
        errors="coerce"
    ).fillna(0)
    df["ASP Profit/Loss"] = pd.to_numeric(
        df["ASP Profit/Loss"]
        .astype(str)
        .str.replace(r"[$,]", "", regex=True),
        errors="coerce"
    ).fillna(0)
    df["AWP Profit/Loss"] = pd.to_numeric(
        df["AWP Profit/Loss"]
        .astype(str)
        .str.replace(r"[$,]", "", regex=True),
        errors="coerce"
    ).fillna(0)

    # Core calculations
    df["ASP per Rx"] = df["Dose_MG"] * df["ASP Profit/Loss"]
    df["AWP per Rx"] = df["Dose_MG"] * df["AWP Profit/Loss"]
    df["ASP All Dispense"] = df["ASP per Rx"] * df["Rx Count"]
    df["AWP All Dispense"] = df["AWP per Rx"] * df["Rx Count"]
    df["Total COGS"] = df["Purchase Price Per Code UOM"] * df["Dose_MG"] * df["Rx Count"]
    df["ASP Revenue"] = df["Total COGS"] + df["ASP All Dispense"]
    df["AWP Revenue"] = df["Total COGS"] + df["AWP All Dispense"]

    # Sidebar inputs for costs and share
    st.sidebar.header("Adjust Costs & Share")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", 0.0, 100.0, 8.0)
    misc_expense = st.sidebar.number_input("Misc Supply Cost per Rx", 0.0, 100.0, 2.0)
    share_pct = st.sidebar.slider("MediHiveRx % Share", 0.0, 100.0, key="green_slider")

    # Sidebar inputs for staffing (Non-MediHive)
    st.sidebar.header("Non-MediHiveRx Staffing")
    ph_headcount = st.sidebar.number_input("Pharmacist Headcount", 0, 10, 1)
    ph_rate = st.sidebar.number_input("Pharmacist Hourly Rate", 0.0, 200.0, 60.0)
    tech_headcount = st.sidebar.number_input("Technician Headcount", 0, 10, 1)
    tech_rate = st.sidebar.number_input("Technician Hourly Rate", 0.0, 100.0, 25.0)
    emr_cost = st.sidebar.number_input("EMR Cost (6m)", 0.0, 100000.0, 3000.0)
    psao_cost = st.sidebar.number_input("PSAO Cost (6m)", 0.0, 50000.0, 2500.0)

    # Compute staffing expense
    ph_cost = ph_headcount * ph_rate * FTE_HOURS_6M
    tech_cost = tech_headcount * tech_rate * FTE_HOURS_6M
    total_staff_cost = ph_cost + tech_cost + emr_cost + psao_cost

    # Compute variable costs
    df["Courier Cost"] = df["Rx Count"] * courier_rate
    df["Misc Cost"] = df["Rx Count"] * misc_expense
    df["Total Variable Cost"] = df["Courier Cost"] + df["Misc Cost"]

    # MediHive scenario
    df_m = df.copy()
    df_m["6M ASP Profit"] = df_m["ASP All Dispense"] - df_m["Total Variable Cost"]
    df_m["6M AWP Profit"] = df_m["AWP All Dispense"] - df_m["Total Variable Cost"]
    df_m["MediHive AWP Share"] = df_m["6M AWP Profit"] * (share_pct / 100)

    # Non-MediHive scenario
    df_n = df.copy()
    df_n["6M ASP Profit"] = df_n["ASP All Dispense"] - df_n["Total Variable Cost"] - (total_staff_cost / len(df_n))
    df_n["6M AWP Profit"] = df_n["AWP All Dispense"] - df_n["Total Variable Cost"] - (total_staff_cost / len(df_n))

    # Display MediHive table
    st.subheader("📋 MediHive Scenario")
    st.dataframe(df_m, use_container_width=True)
    # Summary under MediHive
    tot_rev_asp = df_m["ASP Revenue"].sum()
    tot_pr_asp = df_m["6M ASP Profit"].sum()
    tot_rev_awp = df_m["AWP Revenue"].sum()
    tot_pr_awp = df_m["6M AWP Profit"].sum()
    share_awp = df_m["MediHive AWP Share"].sum()
    net_awp = tot_pr_awp - share_awp

    st.markdown("""
**ASP Revenue:** ${:,.2f}  
**ASP Profit:** ${:,.2f}  
**AWP Revenue:** ${:,.2f}  
**AWP Profit:** ${:,.2f}  
**MediHive Share (AWP):** ${:,.2f}  
**Total AWP Net:** ${:,.2f}
""".format(
        tot_rev_asp, tot_pr_asp, tot_rev_awp, tot_pr_awp, share_awp, net_awp
    ))

    # Display Non-MediHive table
    st.subheader("📋 Non-MediHive Scenario")
    st.dataframe(df_n, use_container_width=True)
    # Summary under Non-MediHive
    tot_pr_nasp = df_n["6M ASP Profit"].sum()
    tot_pr_nawp = df_n["6M AWP Profit"].sum()

    st.markdown("""
**ASP Revenue:** ${:,.2f}  
**ASP Profit:** ${:,.2f}  
**AWP Revenue:** ${:,.2f}  
**AWP Profit:** ${:,.2f}  
**Non-MediHive Expenses:** ${:,.2f}  
**Total AWP Net:** ${:,.2f}
""".format(
        tot_rev_asp, tot_pr_nasp, tot_rev_awp, tot_pr_nawp, total_staff_cost, tot_pr_nawp
    ))

    # Hypothetical simulator
    st.subheader("📊 Hypothetical Revenue & Profit Simulator")
    with st.expander("Try Your Own Revenue + Profit Goals"):
        tgt_rev = st.number_input("Target Total Revenue", 0.0, 1e7)
        tgt_pr = st.number_input("Target Net Profit", 0.0, 1e7)
        if tgt_rev > 0 and tgt_pr > 0:
            margin = tgt_pr / tgt_rev * 100
            st.success(f"To hit ${tgt_pr:,.2f} profit on ${tgt_rev:,.2f} revenue, you need a {margin:.2f}% margin.")
    
    # Explanation
    st.subheader("📘 Calculation Explanations")
    st.markdown("""
- ASP and AWP Profit/Loss loaded from sheet.  
- Revenues include COGS + Profit.  
- Profit % = Profit / Revenue.  
- MediHive share applies to AWP Profit.  
- Non-MediHive expenses include Pharmacist, Technician, EMR, PSAO.
""")
