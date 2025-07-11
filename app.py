import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="MediHiveRx Profitability Tool", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; background-color: #004466; padding: 20px; color: white; border-radius: 8px;'>
        📊 MediHiveRx In-Office Dispensing Profitability Tool
    </h1>
    """, unsafe_allow_html=True)

# --- FILE UPLOAD ---
st.sidebar.header("Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Choose Excel file", type=[".xlsx"])

# --- USER INPUTS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Global Settings")
show_only_profitable = st.sidebar.checkbox("Only Show Profitable Drugs", value=True)
courier_cost_per_rx = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0)
misc_cost_per_rx = st.sidebar.number_input("Misc Supply Cost per Rx", min_value=0.0, value=1.5)
medihive_share_pct = st.sidebar.slider("MediHiveRx Share %", min_value=0, max_value=100, value=20, step=1)

# --- UTILS ---
def clean_currency(series):
    return (
        series.astype(str)
              .str.replace(r"[^\d\-.]", "", regex=True)
              .replace("", "0")
              .astype(float)
    )

def extract_uom(series):
    return pd.to_numeric(series.astype(str)
                             .str.extract(r"(\d+(?:\.\d+)?)")[0],
                      errors='coerce').fillna(1)

def prepare_data(df):
    df = df.copy()
    df['ASP Profit/Loss'] = clean_currency(df['ASP Profit/Loss'])
    df['AWP Profit/Loss'] = clean_currency(df['AWP Profit/Loss'])
    df['Code UOM'] = extract_uom(df['Code UOM'])
    df['Dose'] = pd.to_numeric(df['Dose'], errors='coerce').fillna(0)
    df['Rx Count'] = pd.to_numeric(df['Rx Count'], errors='coerce').fillna(0)
    df['ASP All Dispense'] = df['ASP Profit/Loss'] * df['Rx Count']
    df['AWP All Dispense'] = df['AWP Profit/Loss'] * df['Rx Count']
    return df

# --- MAIN ---
if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    df = prepare_data(df_raw)
    total_rx = df['Rx Count'].sum()

    courier_total = courier_cost_per_rx * total_rx
    misc_total = misc_cost_per_rx * total_rx

    if show_only_profitable:
        df = df[(df['ASP Profit/Loss'] > 0) | (df['AWP Profit/Loss'] > 0)]

    # Format dollar columns for display
    df_display = df.copy()
    for col in ['ASP All Dispense', 'AWP All Dispense']:
        df_display[col] = df_display[col].map('${:,.2f}'.format)

    # MediHiveRx Scenario
    st.subheader('### MediHiveRx Scenario')
    st.data_editor(df_display, use_container_width=True)

    # Financial Summary
    asp_rev = df['ASP All Dispense'].sum()
    awp_rev = df['AWP All Dispense'].sum()
    asp_profit = asp_rev - (courier_total + misc_total)
    awp_profit = awp_rev - (courier_total + misc_total)
    share_amt = awp_profit * (medihive_share_pct / 100)
    net_awp = awp_profit - share_amt

    st.subheader('### Financial Summary – MediHiveRx')
    st.write(f"**ASP Revenue:** ${asp_rev:,.2f}")
    st.write(f"**ASP Profit:** ${asp_profit:,.2f}")
    st.write(f"**AWP Revenue:** ${awp_rev:,.2f}")
    st.write(f"**AWP Profit:** ${awp_profit:,.2f}")
    st.write(f"**MediHiveRx Share (AWP):** ${share_amt:,.2f}")
    st.write(f"**Net AWP:** ${net_awp:,.2f}")

    # Top 5 Profitable Medications (ASP)
    st.markdown('---')
    st.subheader('### Top 5 Profitable Medications (ASP)')
    top5 = df.groupby('Medication')['ASP All Dispense'].sum().nlargest(5)
    st.bar_chart(top5)
    st.dataframe(top5.rename('Total ASP Profit').reset_index())
else:
    st.info('Please upload a data file to begin.')
