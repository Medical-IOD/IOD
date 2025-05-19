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
    df["Purchase Price Per Code UOM"] = pd.to_numeric(df["Purchase Price Per Code UOM"], errors="coerce")

    # Reimbursement Calculations
    df["ASP Reimbursement"] = df["Purchase Price Per Code UOM"] * 1.04
    df["AWP Reimbursement"] = df["Purchase Price Per Code UOM"] * 0.81
    df["ASP Profit/Loss"] = df["ASP Reimbursement"] - df["Purchase Price Per Code UOM"]
    df["AWP Profit/Loss"] = df["AWP Reimbursement"] - df["Purchase Price Per Code UOM"]
    df["ASP per Rx"] = df["Dose_MG"] * df["ASP Profit/Loss"]
    df["AWP per Rx"] = df["Dose_MG"] * df["AWP Profit/Loss"]
    df["ASP All Dispense"] = df["ASP per Rx"] * df["Rx Count"]
    df["AWP All Dispense"] = df["AWP per Rx"] * df["Rx Count"]

    st.sidebar.title("🔧 Adjust Inputs")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0, step=0.5)
    misc_expense = st.sidebar.number_input("Misc. Supply Cost per Rx (Boxes, Bags, Insulation)", min_value=0.0, value=2.0, step=0.5)

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
    df_medi["MediHive ASP Share"] = df_medi["6M ASP Total"] * 0.20
    df_medi["MediHive AWP Share"] = df_medi["6M AWP Total"] * 0.20

    df_nonmedi = df.copy()
    nonmed_total_cost = pharmacist_cost + technician_cost + emr_cost + psao_cost
    df_nonmedi["6M ASP Total"] = df_nonmedi["ASP All Dispense"] - df_nonmedi["Total Variable Cost"] - (nonmed_total_cost / len(df_nonmedi))
    df_nonmedi["6M AWP Total"] = df_nonmedi["AWP All Dispense"] - df_nonmedi["Total Variable Cost"] - (nonmed_total_cost / len(df_nonmedi))

    st.subheader("📋 MediHive Scenario (20% Service Share)")
    st.dataframe(df_medi, use_container_width=True)

    st.subheader("📋 Non-MediHive Scenario (Full Labor Deduction)")
    st.dataframe(df_nonmedi, use_container_width=True)

    st.subheader("📘 Calculation Explanations")
    st.markdown("""
    - **ASP Reimbursement** = Purchase Price Per Code UOM × 1.04  
    - **AWP Reimbursement** = Purchase Price Per Code UOM × 0.81  
    - **ASP Profit/Loss** = ASP Reimbursement − Purchase Price Per Code UOM  
    - **AWP Profit/Loss** = AWP Reimbursement − Purchase Price Per Code UOM  
    - **ASP per Rx** = Dose × ASP Profit/Loss  
    - **AWP per Rx** = Dose × AWP Profit/Loss  
    - **ASP All Dispense** = ASP per Rx × Rx Count  
    - **AWP All Dispense** = AWP per Rx × Rx Count  
    - **Courier Cost** = Rx Count × Courier Rate  
    - **Misc Cost** = Rx Count × Misc Supply Cost  
    - **Total Variable Cost** = Courier + Misc  
    - **MediHive 6M Total** = (ASP or AWP All Dispense − Total Variable Cost)  
    - **MediHive Share** = 20% of MediHive 6M Profit  
    - **Non-MediHive 6M Profit** = (ASP or AWP All Dispense − Total Variable Cost − Total Labor/EMR/PSAO costs)  
    """)

else:
    st.warning("Please upload the profitability Excel file to proceed.")
