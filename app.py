import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

st.set_page_config(page_title="MediHive In-Office Dispensing Pro Forma", layout="wide")

st.markdown("""
    <h1 style='text-align: center; background-color: #2c3e50; padding: 20px; color: white; border-radius: 8px;'>
        💊 MediHive In-Office Dispensing Pro Forma
    </h1>
""", unsafe_allow_html=True)

components.html("""
<style>
input[type=range]::-webkit-slider-thumb {
  background: green;
}
</style>
""", height=0)

uploaded_file = st.sidebar.file_uploader("Upload Profitability Excel", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name="Drug-Profitability")

    df["NDC"] = df["NDC"].astype(str).str.replace("-", "").str.strip()
    df["Strength"] = df["Strength"].astype(str)
    df["Dose_MG"] = df["Strength"].str.extract(r"([\d,.]+)").replace(",", "", regex=True).astype(float)
    df["Rx Count"] = pd.to_numeric(df["Rx Count"], errors="coerce").fillna(0)
    df["Purchase Price Per Code UOM"] = pd.to_numeric(df["Purchase Price Per Code UOM"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce").fillna(0)
    df["ASP Profit/Loss"] = pd.to_numeric(df["ASP Profit/Loss"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce").fillna(0)
    df["AWP Profit/Loss"] = pd.to_numeric(df["AWP Profit/Loss"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce").fillna(0)

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
    medihive_share_percent = st.sidebar.slider("MediHiveRx % Share", min_value=0.0, max_value=100.0, value=20.0, step=1.0, key="green_slider")

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
    st.dataframe(df_medi.fillna(0), use_container_width=True)

    st.subheader("📋 Non-MediHive Scenario")
    st.dataframe(df_nonmedi.fillna(0), use_container_width=True)
else:
    st.warning("Please upload the profitability Excel file to proceed.")
