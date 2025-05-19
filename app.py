import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

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
    df["Purchase Price Per Code UOM"] = pd.to_numeric(df["Purchase Price Per Code UOM"], errors="coerce")

    df["ASP Reimbursement"] = df["Purchase Price Per Code UOM"] * 1.04
    df["AWP Reimbursement"] = df["Purchase Price Per Code UOM"] * 0.81
    df["ASP Profit/Loss"] = df["ASP Reimbursement"] - df["Purchase Price Per Code UOM"]
    df["AWP Profit/Loss"] = df["AWP Reimbursement"] - df["Purchase Price Per Code UOM"]

    st.sidebar.title("🔧 Adjust Inputs")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0, step=0.5)
    misc_expense = st.sidebar.number_input("Misc. Supply Cost per Rx (Boxes, Bags, Insulation)", min_value=0.0, value=2.0, step=0.5)

    st.sidebar.title("🏥 Non-MediHiveRx Factors")
    pharmacist_cost = st.sidebar.number_input("Pharmacist Labor Cost (6 months)", min_value=0.0, step=500.0)
    technician_cost = st.sidebar.number_input("Technician Labor Cost (6 months)", min_value=0.0, step=500.0)
    emr_cost = st.sidebar.number_input("EMR Cost (6 months)", min_value=0.0, step=100.0)
    psao_cost = st.sidebar.number_input("PSAO Cost (6 months)", min_value=0.0, step=100.0)

    editable_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="main_table")

    editable_df["ASP per Rx"] = editable_df["Dose_MG"] * editable_df["ASP Profit/Loss"]
    editable_df["AWP per Rx"] = editable_df["Dose_MG"] * editable_df["AWP Profit/Loss"]
    editable_df["ASP All Dispense"] = editable_df["ASP per Rx"] * editable_df["Rx Count"]
    editable_df["AWP All Dispense"] = editable_df["AWP per Rx"] * editable_df["Rx Count"]
    editable_df["Courier Cost"] = editable_df["Rx Count"] * courier_rate
    editable_df["Misc Cost"] = editable_df["Rx Count"] * misc_expense
    editable_df["Total Variable Cost"] = editable_df["Courier Cost"] + editable_df["Misc Cost"]
    editable_df["6M ASP Total"] = editable_df["ASP All Dispense"] - editable_df["Total Variable Cost"]
    editable_df["6M AWP Total"] = editable_df["AWP All Dispense"] - editable_df["Total Variable Cost"]

    st.subheader("📋 Profitability Table (Editable)")
    st.dataframe(editable_df, use_container_width=True)

    # Base: MediHive share summary (20% of net)
    base_asp = editable_df["6M ASP Total"].sum()
    base_awp = editable_df["6M AWP Total"].sum()
    medihive_asp = base_asp * 0.20
    medihive_awp = base_awp * 0.20

    # With Non-MediHiveRx factors
    other_total_costs = pharmacist_cost + technician_cost + emr_cost + psao_cost
    alt_asp = base_asp - other_total_costs
    alt_awp = base_awp - other_total_costs

    st.subheader("📈 Scenario Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("MediHive 6M ASP Profit", f"${base_asp:,.2f}")
        st.metric("MediHive Share (20%)", f"${medihive_asp:,.2f}")
        st.metric("MediHive 6M AWP Profit", f"${base_awp:,.2f}")
        st.metric("MediHive Share (20%)", f"${medihive_awp:,.2f}")
    with col2:
        st.metric("Non-MediHive ASP Profit (after labor)", f"${alt_asp:,.2f}")
        st.metric("Non-MediHive AWP Profit (after labor)", f"${alt_awp:,.2f}")

    st.subheader("📘 Calculation Explanations")
    st.markdown("""
    - **ASP Profit/Loss** = (Purchase Price per Code UOM × 1.04) − Purchase Price per Code UOM  
    - **AWP Profit/Loss** = (Purchase Price per Code UOM × 0.81) − Purchase Price per Code UOM  
    - **ASP per Rx** = Dose × ASP Profit/Loss  
    - **AWP per Rx** = Dose × AWP Profit/Loss  
    - **ASP All Dispense** = ASP per Rx × Rx Count  
    - **AWP All Dispense** = AWP per Rx × Rx Count  
    - **Courier Cost** = Rx Count × Courier Rate  
    - **Misc Cost** = Rx Count × Miscellaneous Supply Cost  
    - **Total Variable Cost** = Courier Cost + Misc Cost  
    - **6M ASP Total** = ASP All Dispense − Total Variable Cost  
    - **6M AWP Total** = AWP All Dispense − Total Variable Cost  
    - **MediHive Share** = 20% of ASP or AWP Net Profit  
    - **Non-MediHive Total** = 6M Net Profit − (Pharmacist + Technician + EMR + PSAO Costs)  
    """)

else:
    st.warning("Please upload the profitability Excel file to proceed.")
