import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="MediHiveRx Profitability Tool", layout="wide")

# --- HEADER ---
st.markdown("""
<h1 style='text-align: center; background-color: #004466; padding: 20px; color: white; border-radius: 8px;'>
    💊 MediHiveRx In-Office Dispensing Profitability Tool
</h1>
""", unsafe_allow_html=True)

# --- SESSION INIT ---
if "original_data" not in st.session_state:
    st.session_state.original_data = pd.DataFrame()
    st.session_state.medi_data = pd.DataFrame()
    st.session_state.nonmedi_data = pd.DataFrame()
    st.session_state.profit_only = True

# --- FILE UPLOAD ---
st.sidebar.header("Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Choose Excel file", type=[".xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.session_state.original_data = df.copy()
    st.session_state.medi_data = df.copy()
    st.session_state.nonmedi_data = df.copy()

# --- CONTROL PANEL ---
with st.container():
    st.subheader("MediHive Scenario")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Save All Changes", type="primary"):
            st.session_state.original_data = st.session_state.medi_data.copy()
    with col2:
        if st.button("Reset to Original Upload"):
            st.session_state.medi_data = st.session_state.original_data.copy()
            st.session_state.nonmedi_data = st.session_state.original_data.copy()

# --- FILTER TOGGLE ---
st.subheader("Finalized Tables")
st.markdown("Use the toggle to filter for profitable drugs only. Tables are editable. Add rows as needed.")
colA, colB = st.columns([8, 1])
with colB:
    toggle = st.checkbox("Only show profitable drugs", value=st.session_state.profit_only)
    st.session_state.profit_only = toggle

# --- PROFIT FILTER FUNCTION ---
def filter_profitable(df):
    return df[(df["ASP Profit/Loss"] > 0) | (df["AWP Profit/Loss"] > 0)] if st.session_state.profit_only else df

# --- MEDIHIVE TABLE ---
st.markdown("### MediHive Scenario")
st.session_state.medi_data = st.data_editor(
    filter_profitable(st.session_state.medi_data),
    use_container_width=True,
    key="medi_table_editor",
    num_rows="dynamic"
)

# --- NON-MEDIHIVE TABLE ---
st.markdown("### Non-MediHive Scenario")
st.session_state.nonmedi_data = st.data_editor(
    filter_profitable(st.session_state.nonmedi_data),
    use_container_width=True,
    key="nonmedi_table_editor",
    num_rows="dynamic"
)

# --- PLACEHOLDER FOR SUMMARY ---
st.markdown("""
<style>
.summary-box {
    background-color: #001f2e;
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
    color: white;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='summary-box'>
<b>Legend & Formula Summary:</b><br>
- <b>ASP Reimbursement</b> = ASP + 4%<br>
- <b>AWP Reimbursement</b> = AWP - 19%<br>
- <b>Profit per Unit</b> = Reimbursement - Purchase Price Per Code UOM<br>
- <b>Per Rx</b> = Profit per Unit x Dose<br>
- <b>All Dispense</b> = Per Rx x Rx Count<br>
- <b>Total Revenue</b> = Reimbursement x Dose x Rx Count<br>
- <b>Net Profit</b> = Profit - Expenses<br>
</div>
""", unsafe_allow_html=True)
