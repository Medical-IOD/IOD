import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

st.set_page_config(page_title="MediHiveRx Profitability Tool", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; background-color: #004466; padding: 20px; color: white; border-radius: 8px;'>
        📊 MediHiveRx In-Office Dispensing Profitability Tool
    </h1>
    """, unsafe_allow_html=True)

# --- FILE UPLOAD ---
st.sidebar.header("Upload Excel File (must include Dose and Rx Count)")
uploaded_file = st.sidebar.file_uploader("Choose Excel file", type=[".xlsx"])

# --- USER INPUTS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Global Settings")
courier_cost_per_rx = st.sidebar.number_input("Courier Cost per Rx", value=8.0, min_value=0.0)
misc_cost_per_rx = st.sidebar.number_input("Misc Supply Cost per Rx", value=1.5, min_value=0.0)
medihive_share_pct = st.sidebar.slider("MediHiveRx Share %", 0, 100, 20)

# --- UTILITIES ---
def clean_currency(series):
    return (series.astype(str)
                  .str.replace(r"[^\d\-.]", "", regex=True)
                  .replace("", "0")
                  .astype(float))

def prepare_data(df):
    df = df.copy()
    # Numeric conversions
    df['Acq_per_unit'] = clean_currency(df['Acquisition Cost'])
    df['AWP_per_unit'] = clean_currency(df['AWP Profit/Loss'])
    df['Dose'] = pd.to_numeric(df['Dose'], errors='coerce').fillna(0)
    df['Rx_Count'] = pd.to_numeric(df['Rx Count'], errors='coerce').fillna(0)
    # Total units dispensed
    df['Total_Units'] = df['Dose'] * df['Rx_Count']
    # Markup
    brand_list = ['EPICERAM']
    df['Markup_Rate'] = df['Medication'].isin(brand_list).map({True:1.19, False:1.18})
    df['Markedup_Price'] = df['AWP_per_unit'] * df['Markup_Rate']
    # Profit calculations
    df['Net_Profit_per_unit'] = df['Markedup_Price'] - df['Acq_per_unit']
    df['Total_Net_Profit'] = df['Net_Profit_per_unit'] * df['Total_Units']
    return df

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    df = prepare_data(df_raw)

    # Display
    st.subheader("Profit Calculation Table")
    df_display = df[['Medication','Strength','AWP_per_unit','Acq_per_unit',
                     'Markedup_Price','Net_Profit_per_unit','Total_Units','Total_Net_Profit']].copy()
    # Format currency
    for col in ['AWP_per_unit','Acq_per_unit','Markedup_Price','Net_Profit_per_unit','Total_Net_Profit']:
        df_display[col] = df_display[col].map('${:,.2f}'.format)
    st.dataframe(df_display, use_container_width=True)

    # Download
    buffer = BytesIO()
    df_display.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("Download Excel", buffer, file_name="profit_calculations.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("Please upload a properly formatted data file with columns: Medication, Strength,
