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

    st.sidebar.title("🔧 Adjust Inputs")
    courier_rate = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0, step=0.5)
    misc_expense = st.sidebar.number_input("Misc. Supply Cost per Rx (Boxes, Bags, Insulation)", min_value=0.0, value=2.0, step=0.5)
    pharmacist_cost = st.sidebar.number_input("Pharmacist Labor Cost (6 months)", min_value=0.0, value=20000.0, step=500.0)
    technician_cost = st.sidebar.number_input("Technician Labor Cost (6 months)", min_value=0.0, value=15000.0, step=500.0)
    emr_cost = st.sidebar.number_input("EMR Cost (6 months)", min_value=0.0, value=3000.0, step=100.0)
    psao_cost = st.sidebar.number_input("PSAO Cost (6 months)", min_value=0.0, value=2500.0, step=100.0)

    df["ASP per Rx"] = df["Dose_MG"] * df["ASP Profit/Loss"]
    df["AWP per Rx"] = df["Dose_MG"] * df["AWP Profit/Loss"]

    editable_df = st.data_editor(
        df[["Drug Name", "NDC", "HCPCS", "Strength", "Rx Count", "ASP Profit/Loss", "AWP Profit/Loss"]],
        use_container_width=True,
        num_rows="dynamic",
        key="editable_inputs"
    )

    editable_df["ASP per Rx"] = editable_df["Dose_MG"] * editable_df["ASP Profit/Loss"]
    editable_df["AWP per Rx"] = editable_df["Dose_MG"] * editable_df["AWP Profit/Loss"]
    editable_df["ASP All Dispense"] = editable_df["ASP per Rx"] * editable_df["Rx Count"]
    editable_df["AWP All Dispense"] = editable_df["AWP per Rx"] * editable_df["Rx Count"]

    editable_df["Courier Cost"] = editable_df["Rx Count"] * courier_rate
    editable_df["Misc Cost"] = editable_df["Rx Count"] * misc_expense
    editable_df["Total Variable Cost"] = editable_df["Courier Cost"] + editable_df["Misc Cost"]

    editable_df["6M ASP Total"] = editable_df["ASP All Dispense"] - editable_df["Total Variable Cost"]
    editable_df["6M AWP Total"] = editable_df["AWP All Dispense"] - editable_df["Total Variable Cost"]

    st.subheader("📋 Editable Profit Table")
    st.dataframe(editable_df, use_container_width=True)

    total_asp = editable_df["6M ASP Total"].sum()
    total_awp = editable_df["6M AWP Total"].sum()

    dispenser_share_asp = total_asp * 0.80
    medihive_share_asp = total_asp * 0.20

    dispenser_share_awp = total_awp * 0.80
    medihive_share_awp = total_awp * 0.20

    st.subheader("📈 MediHive Scenario Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("6M ASP Net Profit (After All Costs)", f"${total_asp:,.2f}")
        st.metric("MediHive Share (20% ASP)", f"${medihive_share_asp:,.2f}")
    with col2:
        st.metric("6M AWP Net Profit (After All Costs)", f"${total_awp:,.2f}")
        st.metric("MediHive Share (20% AWP)", f"${medihive_share_awp:,.2f}")

    st.subheader("🧾 Non-MediHive Cost Comparison")
    total_other_expense = pharmacist_cost + technician_cost + emr_cost + psao_cost
    st.write("""
    | Category         | Cost ($)       |
    |------------------|----------------|
    | Pharmacist       | ${:,.2f}        |
    | Technician       | ${:,.2f}        |
    | EMR              | ${:,.2f}        |
    | PSAO             | ${:,.2f}        |
    | **Total**        | **${:,.2f}**    |
    """.format(pharmacist_cost, technician_cost, emr_cost, psao_cost, total_other_expense))

    st.markdown("""
    ---
    **Note:** You can now compare MediHive's flat 20% service cost vs. traditional in-house cost categories.
    Adjust Rx counts, courier rate, or ASP values directly above to model various scenarios.
    """)

else:
    st.warning("Please upload the profitability Excel file to proceed.")
