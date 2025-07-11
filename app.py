import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="MediHiveRx Profitability Tool", layout="wide")

# Header
st.markdown("""
<h1 style='text-align: center; background-color: #004466; padding: 20px; color: white; border-radius: 8px;'>
    📊 MediHiveRx In-Office Dispensing Profitability Tool
</h1>
""", unsafe_allow_html=True)

# Sidebar inputs
st.sidebar.header("Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Choose Excel file", type=["xlsx"])
st.sidebar.markdown("---")
st.sidebar.subheader("Global Settings")
courier_cost = st.sidebar.number_input("Courier Cost per Rx", min_value=0.0, value=8.0)
misc_cost    = st.sidebar.number_input("Misc Supply Cost per Rx", min_value=0.0, value=1.5)
medihive_share = st.sidebar.slider("MediHiveRx Share %", 0, 100, 20)
show_only_profitable = st.sidebar.checkbox("Only Show Profitable Drugs", value=True)

@st.cache_data
def clean_currency(series):
    return (series.astype(str)
                  .str.replace(r"[^\d\-.]", "", regex=True)
                  .replace("", "0")
                  .astype(float))

@st.cache_data
def prepare_data(df):
    df = df.copy()
    # Required columns
    for c in ["Medication","Strength","Dose","Rx Count","Acquisition Cost","AWP Profit/Loss"]:
        if c not in df:
            st.error(f"Missing column: {c}")
            return pd.DataFrame()
    # Numeric conversions
    df["Acq_per_unit"] = clean_currency(df["Acquisition Cost"])
    df["AWP_per_unit"] = clean_currency(df["AWP Profit/Loss"])
    df["Dose"]        = pd.to_numeric(df["Dose"], errors="coerce").fillna(0)
    df["Rx_Count"]    = pd.to_numeric(df["Rx Count"], errors="coerce").fillna(0)
    df["Total_Units"] = df["Dose"] * df["Rx_Count"]
    # Markup rates (+19% brand, +18% generic)
    df["Is_Brand"]    = df["Medication"].str.upper().eq("EPICERAM")
    df["Markup_Rate"] = np.where(df["Is_Brand"], 1.19, 1.18)
    df["Markedup_Price"]       = df["AWP_per_unit"] * df["Markup_Rate"]
    # Profit calculations
    df["Net_Profit_per_pkg"]   = df["Markedup_Price"] - df["Acq_per_unit"]
    df["Total_Net_Profit"]     = df["Net_Profit_per_pkg"] * df["Total_Units"]
    return df

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    df = prepare_data(df_raw)
    if df.empty:
        st.stop()
    # Overall metrics
    total_rx = int(df["Rx_Count"].sum())
    courier_total = courier_cost * total_rx
    misc_total    = misc_cost    * total_rx
    acq_total     = (df["Acq_per_unit"] * df["Total_Units"]).sum()
    asp_profit    = df["Total_Net_Profit"].sum()
    awp_profit    = (df["AWP_per_unit"] * df["Total_Units"]).sum() - (courier_total + misc_total + acq_total)
    share_amt     = awp_profit * (medihive_share/100)
    net_awp       = awp_profit - share_amt
    gross_margin  = (asp_profit / acq_total * 100) if acq_total else 0

    # Display KPIs
    cols = st.columns(6)
    cols[0].metric("Total Rx", total_rx)
    cols[1].metric("Total Acquisition", f"${acq_total:,.2f}")
    cols[2].metric("Total ASP Profit",  f"${asp_profit:,.2f}")
    cols[3].metric("Total AWP Profit",  f"${awp_profit:,.2f}")
    cols[4].metric("MediHiveRx Share",  f"${share_amt:,.2f}")
    cols[5].metric("Gross Margin %",    f"{gross_margin:.1f}%")

    # Detailed table
    display = df[[
      "Medication","Strength","Dose","Rx_Count","Total_Units",
      "Acq_per_unit","AWP_per_unit","Markedup_Price",
      "Net_Profit_per_pkg","Total_Net_Profit"
    ]].copy()
    for col in ["Acq_per_unit","AWP_per_unit","Markedup_Price","Net_Profit_per_pkg","Total_Net_Profit"]:
        display[col] = display[col].map("${:,.2f}".format)
    st.subheader("Detailed Table")
    st.data_editor(display, use_container_width=True)

    # Top 5 by profit
    st.subheader("Top 5 by Total Net Profit")
    top5 = df.groupby("Medication")["Total_Net_Profit"].sum().nlargest(5)
    st.bar_chart(top5)

    # Download results
    buf = BytesIO()
    display.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button(
      "Download Results",
      buf,
      file_name="profit_results.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Please upload the provided Excel file to begin.")
