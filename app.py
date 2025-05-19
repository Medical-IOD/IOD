import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="MediHive In-Office Dispensing Pro Forma", layout="wide")

st.markdown("""
    <h1 style='text-align: center; background-color: #2c3e50; padding: 20px; color: white; border-radius: 8px;'>
        💊 MediHive In-Office Dispensing Pro Forma
    </h1>
""", unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader("Upload Profitability Excel", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name="Drug-Profitability")

    df["NDC"] = df["NDC"].astype(str).str.replace("-", "").str.strip()
    df["Strength"] = df["Strength"].astype(str)
    df["Dose_MG"] = df["Strength"].str.extract(r"([\d,.]+)").replace(",", "", regex=True).astype(float)
    df["Rx Count"] = pd.to_numeric(df["Rx Count"], errors="coerce")
    df["Purchase Price Per Code UOM"] = pd.to_numeric(df["Purchase Price Per Code UOM"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["ASP Profit/Loss"] = pd.to_numeric(df["ASP Profit/Loss"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["AWP Profit/Loss"] = pd.to_numeric(df["AWP Profit/Loss"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")

    df["ASP per Rx"] = df["Dose_MG"] * df["ASP Profit/Loss"]
    df["AWP per Rx"] = df["Dose_MG"] * df["AWP Profit/Loss"]
    df["ASP All Dispense"] = df["ASP per Rx"] * df["Rx Count"]
    df["AWP All Dispense"] = df["AWP per Rx"] * df["Rx Count"]
    df["Total COGS"] = df["Purchase Price Per Code UOM"] * df["Dose_MG"] * df["Rx Count"]
    df["ASP Revenue"] = df["Total COGS"] + df["ASP All Dispense"]
    df["AWP Revenue"] = df["Total COGS"] + df["AWP All Dispense"]

    st.sidebar.title("🔧 Adjust Inputs")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0, step=0.5)
    misc_expense = st.sidebar.number_input("Misc. Supply Cost per Rx", min_value=0.0, value=2.0, step=0.5)
    medihive_share_percent = st.sidebar.slider("MediHiveRx % Share", min_value=0.0, max_value=100.0, value=20.0, step=1.0)

    st.sidebar.title("🏥 Non-MediHiveRx Factors")
    pharmacist_cost = st.sidebar.number_input("Pharmacist Labor Cost (6 months)", min_value=0.0, step=500.0)
    technician_cost = st.sidebar.number_input("Technician Labor Cost (6 months)", min_value=0.0, step=500.0)
    emr_cost = st.sidebar.number_input("EMR Cost (6 months)", min_value=0.0, step=100.0)
    psao_cost = st.sidebar.number_input("PSAO Cost (6 months)", min_value=0.0, step=100.0)

    df["Courier Cost"] = df["Rx Count"] * courier_rate
    df["Misc Cost"] = df["Rx Count"] * misc_expense
    df["Total Variable Cost"] = df["Courier Cost"] + df["Misc Cost"]

    df_medi = df.copy()
    df_medi["6M ASP Total"] = df_medi["ASP All Dispense"] - df_medi["Total Variable Cost"]
    df_medi["6M AWP Total"] = df_medi["AWP All Dispense"] - df_medi["Total Variable Cost"]
    df_medi["MediHive ASP Share"] = df_medi["6M ASP Total"] * (medihive_share_percent / 100)
    df_medi["MediHive AWP Share"] = df_medi["6M AWP Total"] * (medihive_share_percent / 100)

    df_nonmedi = df.copy()
    total_nonmedi_expense = pharmacist_cost + technician_cost + emr_cost + psao_cost
    df_nonmedi["6M ASP Total"] = df_nonmedi["ASP All Dispense"] - df_nonmedi["Total Variable Cost"] - (total_nonmedi_expense / len(df_nonmedi))
    df_nonmedi["6M AWP Total"] = df_nonmedi["AWP All Dispense"] - df_nonmedi["Total Variable Cost"] - (total_nonmedi_expense / len(df_nonmedi))

    st.subheader("📋 MediHive Scenario")
    st.dataframe(df_medi, use_container_width=True)
    total_medi_asp = df_medi["6M ASP Total"].sum()
    total_medi_awp = df_medi["6M AWP Total"].sum()
    share_asp = df_medi["MediHive ASP Share"].sum()
    share_awp = df_medi["MediHive AWP Share"].sum()
    net_medi_asp = total_medi_asp - share_asp
    net_medi_awp = total_medi_awp - share_awp
    revenue_medi_asp = df_medi["ASP Revenue"].sum()
    revenue_medi_awp = df_medi["AWP Revenue"].sum()

    st.markdown(f"**Total ASP Revenue:** ${revenue_medi_asp:,.2f}")
    st.markdown(f"**Total ASP Profit:** ${total_medi_asp:,.2f} → Profit %: {(total_medi_asp / revenue_medi_asp * 100):.2f}%")
    st.markdown(f"** ASP 20% ({medihive_share_percent:.0f}%):** ${share_asp:,.2f}")
    st.markdown(f"**Net ASP Profit:** ${net_medi_asp:,.2f}")

    st.markdown("---")

    st.markdown(f"**Total AWP Revenue:** ${revenue_medi_awp:,.2f}")
    st.markdown(f"**Total AWP Profit:** ${total_medi_awp:,.2f} → Profit %: {(total_medi_awp / revenue_medi_awp * 100):.2f}%")
    st.markdown(f"**MediHive AWP Share ({medihive_share_percent:.0f}%):** ${share_awp:,.2f}")
    st.markdown(f"**Net MediHive AWP Profit:** ${net_medi_awp:,.2f}")

    st.subheader("📋 Non-MediHive Scenario")
    st.dataframe(df_nonmedi, use_container_width=True)
    total_nonmedi_asp = df_nonmedi["6M ASP Total"].sum()
    total_nonmedi_awp = df_nonmedi["6M AWP Total"].sum()
    revenue_nonmedi_asp = df["ASP Revenue"].sum()
    revenue_nonmedi_awp = df["AWP Revenue"].sum()

    st.markdown(f"**Total ASP Revenue:** ${revenue_nonmedi_asp:,.2f}")
    st.markdown(f"**Total ASP Profit:** ${total_nonmedi_asp:,.2f} → Profit %: {(total_nonmedi_asp / revenue_nonmedi_asp * 100):.2f}%")
    st.markdown(f"**Non-MediHive Total Expenses (6M):** ${total_nonmedi_expense:,.2f}")

    st.markdown("---")

    st.markdown(f"**Total AWP Revenue:** ${revenue_nonmedi_awp:,.2f}")
    st.markdown(f"**Total AWP Profit:** ${total_nonmedi_awp:,.2f} → Profit %: {(total_nonmedi_awp / revenue_nonmedi_awp * 100):.2f}%")
    st.markdown(f"**Non-MediHive Total Expenses (6M):** ${total_nonmedi_expense:,.2f}")

    st.subheader("📊 Hypothetical Revenue & Profit Simulator")
    with st.expander("Try Your Own Revenue + Margin Goals"):
        hypo_revenue = st.number_input("Enter Target Total Revenue ($)", min_value=0.0, step=1000.0)
        hypo_profit = st.number_input("Enter Target Net Profit ($)", min_value=0.0, step=100.0)
        if hypo_revenue > 0 and hypo_profit > 0:
            hypo_margin = (hypo_profit / hypo_revenue) * 100
            st.success(f"To achieve ${hypo_profit:,.2f} profit from ${hypo_revenue:,.2f} revenue, you need a margin of {hypo_margin:.2f}%")

    st.subheader("📘 Calculation Explanations")
    st.markdown("""
    - **ASP Profit/Loss** and **AWP Profit/Loss** are loaded directly from your uploaded sheet.  
    - **ASP per Rx** = Total Unit of Measure × ASP Profit/Loss  
    - **AWP per Rx** = Total Unit of Measure × AWP Profit/Loss  
    - **ASP All Dispense** = ASP per Rx × Rx Count  
    - **AWP All Dispense** = AWP per Rx × Rx Count  
    - **COGS** = Purchase Price × Unit × Rx Count  
    - **Revenue** = COGS + Profit (for both ASP and AWP)  
    - **Profit %** = Profit ÷ Revenue  
    - **Courier Cost** = Rx Count × Courier Rate  
    - **Misc Cost** = Rx Count × Misc Supply Cost  
    - **Total Variable Cost** = Courier + Misc  
    - **MediHive Share** = MediHive % × ASP or AWP Profit (after variable costs)  
    - **Non-MediHive Cost** = Pharmacist + Tech + EMR + PSAO  
    """)

else:
    st.warning("Please upload the profitability Excel file to proceed.")
