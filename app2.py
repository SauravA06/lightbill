import streamlit as st
from logic import (
    init_db,
    calculate_bill,
    get_previous_reading,
    update_readings,
    is_initialized,
    get_history,
    reset_db
)
from datetime import datetime

st.set_page_config(page_title="Electricity Bill Calculator", layout="wide")
st.title("⚡ Electricity Bill Calculator")
st.caption("3 Tenants + Shared Water Motor")

# ---------- INIT DB ---------- #
init_db()

# ---------- RESET DATABASE BUTTON ---------- #
if st.button("⚠️ Reset Database (Start Fresh)"):
    reset_db()
    st.warning("Database reset! Reload the page to start first-time setup.")
    st.stop()

# ---------- FUNCTION TO PICK MONTH AND YEAR (Date = 3rd) ---------- #
def select_month_year(label, key_name):
    st.subheader(label)
    col1, col2 = st.columns(2)
    with col1:
        month_input = st.selectbox(
            "Select Month",
            options=[
                "Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"
            ],
            index=datetime.now().month - 1,
            key=f"{key_name}_month"
        )
    with col2:
        current_year = datetime.now().year
        year_input = st.number_input(
            "Select Year",
            min_value=2000,
            max_value=2100,
            value=current_year,
            step=1,
            key=f"{key_name}_year"
        )
    # Internally set date to 3rd
    month_number = datetime.strptime(month_input, "%b").month
    date_obj = datetime(year_input, month_number, 3)
    return date_obj.strftime("%b-%Y")  # e.g., Oct-2025

# ---------- FIRST-TIME SETUP ---------- #
if not is_initialized():
    st.warning("First-time setup: Enter initial meter readings")
    month_str = select_month_year("Select Month & Year for Initial Readings", key_name="init")

    t1_init = st.number_input("Tenant 1 Initial Reading", min_value=0)
    t2_init = st.number_input("Tenant 2 Initial Reading", min_value=0)
    t3_init = st.number_input("Tenant 3 Initial Reading", min_value=0)
    water_init = st.number_input("Water Motor Initial Reading", min_value=0)

    if st.button("Save Initial Readings"):
        update_readings({
            't1': t1_init,
            't2': t2_init,
            't3': t3_init,
            'water': water_init
        }, month=month_str)
        st.success("Initial readings saved. Reload the page to continue.")
        st.stop()

# ---------- NORMAL FLOW ---------- #
st.success("Previous month readings loaded automatically")

prev = {
    't1': get_previous_reading('t1'),
    't2': get_previous_reading('t2'),
    't3': get_previous_reading('t3'),
    'water': get_previous_reading('water')
}

month_str = select_month_year("Select Month & Year for Current Readings", key_name="current")

st.subheader("Enter Current Readings")
current = {}
current['t1'] = st.number_input("Tenant 1", min_value=prev['t1'])
current['t2'] = st.number_input("Tenant 2", min_value=prev['t2'])
current['t3'] = st.number_input("Tenant 3", min_value=prev['t3'])
current['water'] = st.number_input("Water Motor", min_value=prev['water'])

# Optional: actual total bill
st.subheader("Optional: Enter Actual Total Bill Amount (₹)")
actual_bill_input = st.number_input(
    "Amount Paid to Government", min_value=0, value=0
)

if st.button("Calculate Bill"):
    if actual_bill_input > 0:
        bills = calculate_bill(current, actual_total_bill=actual_bill_input)
    else:
        bills = calculate_bill(current)

    st.subheader("Final Bill")
    cols = st.columns(3)

    for col, tenant in zip(cols, ['t1','t2','t3']):
        with col:
            st.info(f"Tenant {tenant[-1]}")
            st.write(f"Units: **{bills[tenant]['units']}**")
            st.write(f"Amount: **₹{bills[tenant]['amount']}**")

    # Save readings with selected month-year
    update_readings(current, month_str)
    st.success("Readings saved for the selected month ✅")

# ---------- HISTORY DISPLAY ---------- #
st.subheader("📜 Meter Reading History")
for tenant in ['t1','t2','t3','water']:
    st.markdown(f"**{tenant.upper()} History**")
    hist = get_history(tenant)
    st.table(hist)
