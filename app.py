import streamlit as st
import pandas as pd
import numpy as np

# Constants
FTE_HOURS_6M = 40 * 52 / 2  # 40 hr/week * 52 weeks/year /2 = 1040 hours for 6 months

st.set_page_config(page_title="MediHive In-Office Dispensing Pro Forma", layout="wide")

# Custom slider CSS for green thumb
st.markdown("""
<style>
/* Slider thumb green */
input[type=range]::-webkit-slider-thumb {
  background: #2ecc71;
}
input[type=range]::-moz-range-thumb {
  background: #2ecc71;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center; background-color: #2c3e50; padding: 20px; color: white; border-radius: 8px;'>
        💊 MediHive In-Office Dispensing Pro Forma
    </h1>
""", unsafe_allow_html=True)

# File upload
uploaded_file = st.sidebar.file_uploader("Upload Profitability Excel", type=["xlsx"])
if uploaded_file is not None:
    # Load data
    df = pd.read_excel(uploaded_file, sheet_name="Drug-Profitability")
    # Clean and convert necessary columns, keep negatives
    df["Dose_MG"] = pd.to_numeric(df["Strength"].astype(str).str.extract(r"([\d,.]+)")[0].str.replace(",", ""), errors="coerce")
    df["Rx Count"] = pd.to_numeric(df["Rx Count"], errors="coerce").fillna(0)
    df["Purchase Price Per Code UOM"] = pd.to_numeric(df["Purchase Price Per Code UOM"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["ASP Profit/Loss"] = pd.to_numeric(df["ASP Profit/Loss"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["AWP Profit/Loss"] = pd.to_numeric(df["AWP Profit/Loss"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")

    # Calculated columns
    df["ASP per Rx"] = df["Dose_MG"] * df["ASP Profit/Loss"]
    df["AWP per Rx"] = df["Dose_MG"] * df["AWP Profit/Loss"]
    df["ASP All Dispense"] = df["ASP per Rx"] * df["Rx Count"]
    df["AWP All Dispense"] = df["AWP per Rx"] * df["Rx Count"]
    df["Total COGS"] = df["Purchase Price Per Code UOM"] * df["Dose_MG"] * df["Rx Count"]
    df["ASP Revenue"] = df["Total COGS"] + df["ASP All Dispense"]
    df["AWP Revenue"] = df["Total COGS"] + df["AWP All Dispense"]

    # Sidebar inputs
    st.sidebar.header("🔧 Adjust Inputs")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0, step=0.5)
    misc_expense = st.sidebar.number_input("Misc. Supply Cost per Rx", min_value=0.0, value=2.0, step=0.5)
    medihive_share_percent = st.sidebar.slider("MediHiveRx % Share", min_value=0.0, max_value=100.0, value=20.0, step=1.0)

    st.sidebar.header("🏥 Non-MediHiveRx Factors")
    pharmacist_count = st.sidebar.number_input("Pharmacist Headcount", min_value=0, step=1)
    pharmacist_rate = st.sidebar.number_input("Pharmacist Hourly Rate ($)", min_value=0.0, step=1.0)
    technician_count = st.sidebar.number_input("Technician Headcount", min_value=0, step=1)
    technician_rate = st.sidebar.number_input("Technician Hourly Rate ($)", min_value=0.0, step=1.0)
    emr_cost = st.sidebar.number_input("EMR Cost (6 months)", min_value=0.0, step=100.0)
    psao_cost = st.sidebar.number_input("PSAO Cost (6 months)", min_value=0.0, step=100.0)

    # Compute costs
    df["Courier Cost"] = df["Rx Count"] * courier_rate
    df["Misc Cost"] = df["Rx Count"] * misc_expense
    df["Total Variable Cost"] = df["Courier Cost"] + df["Misc Cost"]

    pharma_cost = pharmacist_count * pharmacist_rate * FTE_HOURS_6M
    tech_cost = technician_count * technician_rate * FTE_HOURS_6M
    total_nonmedi_expense = pharma_cost + tech_cost + emr_cost + psao_cost

    # MediHive scenario
    df_medi = df.copy()
    df_medi["6M ASP Profit"] = df_medi["ASP All Dispense"] - df_medi["Total Variable Cost"]
    df_medi["6M AWP Profit"] = df_medi["AWP All Dispense"] - df_medi["Total Variable Cost"]
    df_medi["MediHive ASP Share"] = df_medi["6M ASP Profit"] * (medihive_share_percent/100)
    df_medi["MediHive AWP Share"] = df_medi["6M AWP Profit"] * (medihive_share_percent/100)

    # Non-MediHive scenario
    df_nonmedi = df.copy()
    df_nonmedi["6M ASP Profit"] = df_nonmedi["ASP All Dispense"] - df_nonmedi["Total Variable Cost"] - (total_nonmedi_expense/len(df_nonmedi))
    df_nonmedi["6M AWP Profit"] = df_nonmedi["AWP All Dispense"] - df_nonmedi["Total Variable Cost"] - (total_nonmedi_expense/len(df_nonmedi))

    # Display MediHive table
    st.subheader("📋 MediHive Scenario")
    st.dataframe(df_medi, use_container_width=True)
    tot_rev_asp = df_medi["ASP Revenue"].sum()
    tot_prof_asp = df_medi["6M ASP Profit"].sum()
    profit_pct_asp = (tot_prof_asp/tot_rev_asp*100) if tot_rev_asp else 0
    share_asp = df_medi["MediHive ASP Share"].sum()
    net_prof_asp = tot_prof_asp - share_asp

    st.markdown(f"**Total ASP Revenue:** ${tot_rev_asp:,.2f}")
    st.markdown(f"**Total ASP Profit:** ${tot_prof_asp:,.2f} ({profit_pct_asp:.2f}%)")
    st.markdown(f"**MediHive ASP Share ({medihive_share_percent:.0f}%):** ${share_asp:,.2f}")
    st.markdown(f"**Net MediHive ASP Profit:** ${net_prof_asp:,.2f}")

    # Display Non-MediHive table
    st.subheader("📋 Non-MediHive Scenario")
    st.dataframe(df_nonmedi, use_container_width=True)
    tot_rev_asp_nm = df_nonmedi["ASP Revenue"].sum()
    tot_prof_asp_nm = df_nonmedi["6M ASP Profit"].sum()
    profit_pct_asp_nm = (tot_prof_asp_nm/tot_rev_asp_nm*100) if tot_rev_asp_nm else 0

    st.markdown(f"**Total ASP Revenue:** ${tot_rev_asp_nm:,.2f}")
    st.markdown(f"**Total ASP Profit:** ${tot_prof_asp_nm:,.2f} ({profit_pct_asp_nm:.2f}%)")
    st.markdown(f"**Non-MediHive Total Expenses (6M):** ${total_nonmedi_expense:,.2f}")

    # Hypothetical simulator
    st.subheader("📊 Hypothetical Revenue & Profit Simulator")
    with st.expander("Try Your Own Revenue + Margin Goals"):
        hypo_revenue = st.number_input("Enter Target Total Revenue ($)", min_value=0.0, step=1000.0)
        hypo_profit = st.number_input("Enter Target Net Profit ($)", min_value=0.0, step=100.0)
        if hypo_revenue and hypo_profit:
            hypo_pct = hypo_profit / hypo_revenue * 100
            st.success(f"A profit of ${hypo_profit:,.2f} on revenue ${hypo_revenue:,.2f} is {hypo_pct:.2f}% margin.")

else:
    st.warning("Please upload the profitability Excel file to proceed.")
