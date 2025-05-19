
# This file was auto-generated and corresponds to the Streamlit app updated earlier
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
    df["ASP Profit/Loss"] = pd.to_numeric(df["ASP Profit/Loss"].astype(str).str.replace("[$,()]", "", regex=True).str.replace(")", "-"), errors="coerce")
    df["AWP Profit/Loss"] = pd.to_numeric(df["AWP Profit/Loss"].astype(str).str.replace("[$,()]", "", regex=True).str.replace(")", "-"), errors="coerce")
    df["Rx Count"] = pd.to_numeric(df["Rx Count"], errors="coerce")

    df["ASP per Rx"] = df["Dose_MG"] * df["ASP Profit/Loss"]
    df["AWP per Rx"] = df["Dose_MG"] * df["AWP Profit/Loss"]
    df["ASP All Dispense"] = df["ASP per Rx"] * df["Rx Count"]
    df["AWP All Dispense"] = df["AWP per Rx"] * df["Rx Count"]
    df["Courier Cost"] = df["Rx Count"] * 8
    df["6M ASP Total"] = df["ASP All Dispense"] - df["Courier Cost"]
    df["6M AWP Total"] = df["AWP All Dispense"] - df["Courier Cost"]

    st.sidebar.title("🔧 Adjust Inputs")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0, step=0.5)
    df["Courier Cost"] = df["Rx Count"] * courier_rate
    df["6M ASP Total"] = df["ASP All Dispense"] - df["Courier Cost"]
    df["6M AWP Total"] = df["AWP All Dispense"] - df["Courier Cost"]

    st.subheader("📋 Editable Profit Table")
    edited_df = st.data_editor(
        df[["Drug Name", "HCPCS", "NDC", "Strength", "Dose_MG", "Rx Count", "ASP Profit/Loss", "AWP Profit/Loss", "Courier Cost", "6M ASP Total", "6M AWP Total"]],
        use_container_width=True,
        num_rows="dynamic",
        key="editor"
    )

    total_asp = edited_df["6M ASP Total"].sum()
    total_awp = edited_df["6M AWP Total"].sum()

    dispenser_share_asp = total_asp * 0.80
    medihive_share_asp = total_asp * 0.20

    dispenser_share_awp = total_awp * 0.80
    medihive_share_awp = total_awp * 0.20

    st.subheader("📈 Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("6M ASP Net Profit (After Courier)", f"${total_asp:,.2f}")
        st.metric("MediHive Share (20% ASP)", f"${medihive_share_asp:,.2f}")
    with col2:
        st.metric("6M AWP Net Profit (After Courier)", f"${total_awp:,.2f}")
        st.metric("MediHive Share (20% AWP)", f"${medihive_share_awp:,.2f}")

    st.markdown("""
    ---
    **Note:** This pro forma includes estimated profitability for 6 months of dispensing.
    Courier cost is deducted from total revenue. MediHive receives 20% of the net total to cover labor, EMR, and management support.
    """)
else:
    st.warning("Please upload the profitability Excel file to proceed.")
