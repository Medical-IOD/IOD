import streamlit as st
import pandas as pd
import numpy as np

# Constants
FTE_HOURS_6M = 40 * 52 / 2  # 1040 hours in 6 months per FTE

st.set_page_config(page_title="MediHive In-Office Dispensing Pro Forma", layout="wide")

# Green slider thumb
st.markdown("""
<style>
input[type=range]::-webkit-slider-thumb { background: #2ecc71 !important; }
input[type=range]::-moz-range-thumb { background: #2ecc71 !important; }
</style>
""", unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader("Upload Profitability Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Drug-Profitability")

    # Clean & convert
    df["NDC"] = df['NDC'].astype(str).str.replace('-', '').str.strip()
    df["Dose_MG"] = df['Strength'].astype(str).str.extract(r"([\d,.]+)")[0].str.replace(',', '').astype(float)
    df['Rx Count'] = pd.to_numeric(df['Rx Count'], errors='coerce').fillna(0)
    df['Purchase Price Per Code UOM'] = pd.to_numeric(df['Purchase Price Per Code UOM']
        .astype(str).str.replace('[$,]', ''), errors='coerce')
    df['ASP Profit/Loss'] = pd.to_numeric(df['ASP Profit/Loss']
        .astype(str).str.replace('[$,]', ''), errors='coerce')
    df['AWP Profit/Loss'] = pd.to_numeric(df['AWP Profit/Loss']
        .astype(str).str.replace('[$,]', ''), errors='coerce')

    # Calculations
    df['ASP per Rx'] = df['Dose_MG'] * df['ASP Profit/Loss']
    df['AWP per Rx'] = df['Dose_MG'] * df['AWP Profit/Loss']
    df['ASP All Dispense'] = df['ASP per Rx'] * df['Rx Count']
    df['AWP All Dispense'] = df['AWP per Rx'] * df['Rx Count']
    df['Total COGS'] = df['Purchase Price Per Code UOM'] * df['Dose_MG'] * df['Rx Count']
    df['ASP Revenue'] = df['Total COGS'] + df['ASP All Dispense']
    df['AWP Revenue'] = df['Total COGS'] + df['AWP All Dispense']

    # Sidebar inputs
    st.sidebar.header("Adjust Costs & Share")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", 0.0, 100.0, 8.0)
    misc_expense = st.sidebar.number_input("Misc Supply Cost per Rx", 0.0, 100.0, 2.0)
    share_pct = st.sidebar.slider("MediHiveRx % Share", 0.0, 100.0, 20.0)

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

    # Variable costs
    df['Courier Cost'] = df['Rx Count'] * courier_rate
    df['Misc Cost'] = df['Rx Count'] * misc_expense
    df['Total Variable Cost'] = df['Courier Cost'] + df['Misc Cost']

    # MediHive scenario
    df_m = df.copy()
    df_m['6M ASP Profit'] = df_m['ASP All Dispense'] - df_m['Total Variable Cost']
    df_m['6M AWP Profit'] = df_m['AWP All Dispense'] - df_m['Total Variable Cost']
    df_m['MediHive ASP Share'] = df_m['6M ASP Profit'] * (share_pct/100)
    df_m['MediHive AWP Share'] = df_m['6M AWP Profit'] * (share_pct/100)

    # Non-MediHive scenario
    df_n = df.copy()
    df_n['6M ASP Profit'] = df_n['ASP All Dispense'] - df_n['Total Variable Cost'] - total_staff_cost/len(df_n)
    df_n['6M AWP Profit'] = df_n['AWP All Dispense'] - df_n['Total Variable Cost'] - total_staff_cost/len(df_n)

    # Display MediHive table
    st.subheader("MediHive Scenario")
    st.dataframe(df_m.fillna(0), use_container_width=True)
    # Summaries
    tot_rev_asp = df_m['ASP Revenue'].sum()
    tot_rev_awp = df_m['AWP Revenue'].sum()
    tot_pr_asp = df_m['6M ASP Profit'].sum()
    tot_pr_awp = df_m['6M AWP Profit'].sum()
    share_asp = df_m['MediHive ASP Share'].sum()
    share_awp = df_m['MediHive AWP Share'].sum()
    net_asp = tot_pr_asp - share_asp
    net_awp = tot_pr_awp - share_awp

    st.markdown(f"**ASP Revenue:** ${tot_rev_asp:,.2f} | **Profit:** ${tot_pr_asp:,.2f} ({tot_pr_asp/tot_rev_asp*100:.2f}%)")
    st.markdown(f"**MediHive Share:** ${share_asp:,.2f} | **Net ASP Profit:** ${net_asp:,.2f}")
    st.markdown(f"**AWP Revenue:** ${tot_rev_awp:,.2f} | **Profit:** ${tot_pr_awp:,.2f} ({tot_pr_awp/tot_rev_awp*100:.2f}%)")
    st.markdown(f"**MediHive Share:** ${share_awp:,.2f} | **Net AWP Profit:** ${net_awp:,.2f}")

    # Display Non-MediHive table
    st.subheader("Non-MediHive Scenario")
    st.dataframe(df_n.fillna(0), use_container_width=True)
    tot_pr_nasp = df_n['6M ASP Profit'].sum()
    tot_pr_nawp = df_n['6M AWP Profit'].sum()
    st.markdown(f"**Profit ASP:** ${tot_pr_nasp:,.2f} ({tot_pr_nasp/tot_rev_asp*100:.2f}%)")
    st.markdown(f"**Profit AWP:** ${tot_pr_nawp:,.2f} ({tot_pr_nawp/tot_rev_awp*100:.2f}%)")
    st.markdown(f"**Total Staff/Admin Cost:** ${total_staff_cost:,.2f}")

    # Hypothetical simulator
    st.subheader("Hypothetical Simulator")
    with st.expander("Enter Target Revenue & Profit"):
        tgt_rev = st.number_input("Target Total Revenue", 0.0, 1e7, 0.0)
        tgt_pr = st.number_input("Target Net Profit", 0.0, 1e7, 0.0)
        if tgt_rev>0 and tgt_pr>0:
            margin = tgt_pr/tgt_rev*100
            st.success(f"Target Profit Margin = {margin:.2f}%")

else:
    st.info("Upload the profitability Excel to start.")
