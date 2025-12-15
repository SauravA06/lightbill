import streamlit as st
import pandas as pd
from datetime import datetime
from logic import (
    init_db,
    calculate_bill,
    get_previous_reading,
    update_readings,
    is_initialized,
    get_full_history,
    reset_db
)

st.set_page_config(page_title="Electricity Bill Calculator", layout="wide")

# ---------- TOP ---------- #
st.markdown("<h1 style='text-align: center;'>⚡ Electricity Bill Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ---------- INIT DB ---------- #
init_db()

# ---------- PASSWORD SECTION ---------- #
st.markdown("<h4 style='text-align: center;'>Enter Admin Password</h4>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,2,1])

with col2:
    password = st.text_input(
        "",
        type="password",
        key="pwd",
        placeholder="Password"
    )

    login_clicked = st.button("Login", use_container_width=True)

if login_clicked:
    admin_pass = st.secrets["ADMIN_PASSWORD"]
    if password == admin_pass:
        st.success("✅ Admin Access Granted!")
        st.session_state["admin"] = True
    else:
        st.error("❌ Incorrect password")


# ---------- ADMIN LOGIC ---------- #
if st.session_state.get("admin", False):

    # ---------- SELECT MONTH & YEAR ---------- #
    def select_month_year(label, key_name):
        st.subheader(label)
        col1, col2 = st.columns(2)
        with col1:
            month_input = st.selectbox(
                "Month",
                options=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
                index=datetime.now().month - 1,
                key=f"{key_name}_month"
            )
        with col2:
            current_year = datetime.now().year
            year_input = st.number_input(
                "Year",
                min_value=2000,
                max_value=2100,
                value=current_year,
                step=1,
                key=f"{key_name}_year"
            )
        month_number = datetime.strptime(month_input, "%b").month
        date_obj = datetime(year_input, month_number, 3)
        return date_obj.strftime("%b-%Y")

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

    st.success("Previous month readings loaded automatically")

    prev = {m: get_previous_reading(m) for m in ['t1','t2','t3','water']}
    month_str = select_month_year("Select Month & Year for Current Readings", key_name="current")

    st.subheader("Enter Current Readings")
    current = {}
    current['t1'] = st.number_input("Tenant 1", min_value=prev['t1'])
    current['t2'] = st.number_input("Tenant 2", min_value=prev['t2'])
    current['t3'] = st.number_input("Tenant 3", min_value=prev['t3'])
    current['water'] = st.number_input("Water Motor", min_value=prev['water'])

    st.subheader("Optional: Enter Actual Total Bill Amount (₹)")
    actual_bill_input = st.number_input("Amount Paid to MSEDCL", min_value=0, value=0)

    if st.button("Calculate Bill"):
        if actual_bill_input > 0:
            bills = calculate_bill(current, actual_total_bill=actual_bill_input)
        else:
            bills = calculate_bill(current)

        st.subheader("Final Bill")
        # Only tenants (exclude water)
tenant_keys = ['t1', 't2', 't3']

amounts_sorted = sorted(
    [(k, bills[k]['amount']) for k in tenant_keys],
    key=lambda x: x[1]
)

# Pastel color palette
PASTEL_COLORS = {
    "green": {
        "bg": "#E8F5E9",
        "text": "#1B5E20"
    },
    "yellow": {
        "bg": "#FFF8E1",
        "text": "#6D4C00"
    },
    "red": {
        "bg": "#FDECEA",
        "text": "#7F1D1D"
    }
}

color_rank = {
    amounts_sorted[0][0]: "green",   # lowest bill
    amounts_sorted[1][0]: "yellow",  # medium bill
    amounts_sorted[2][0]: "red"      # highest bill
}

cols = st.columns(3)
amounts_to_save = {}

for col, tenant in zip(cols, ['t1', 't2', 't3']):
    with col:
        theme = PASTEL_COLORS[color_rank[tenant]]
        st.markdown(
            f"""
            <div style="
                background-color:{theme['bg']};
                padding:16px;
                border-radius:12px;
                border-left:6px solid {theme['text']};
            ">
                <h4 style="color:{theme['text']}; margin-bottom:8px;">
                    Tenant {tenant[-1]}
                </h4>
                <p style="margin:4px 0; color:{theme['text']};">
                    Units Consumed: <b>{bills[tenant]['units']}</b>
                </p>
                <p style="margin:4px 0; color:{theme['text']};">
                    Amount Payable: <b>₹{bills[tenant]['amount']}</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        amounts_to_save[tenant] = bills[tenant]['amount']
        update_readings(current, month_str, amounts=amounts_to_save)
        st.success("Readings saved for the selected month ✅")

# ---------- BOTTOM: HISTORY ---------- #
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("📊 Recent 2 Months Summary (Tenant-wise)")

history = get_full_history()
if history:
    df = pd.DataFrame(history, columns=["Meter","Month","Reading","Amount"])
    # Pivot table: months as rows, tenants+water as columns
    pivot = df.pivot_table(index='Month', columns='Meter', values=['Reading','Amount'], aggfunc='first')

    # Add ₹ symbol to Amount columns
    for col in pivot.columns:
        if col[0] == 'Amount':
            pivot[col] = pivot[col].apply(lambda x: f"₹{x}" if pd.notnull(x) else "")

    pivot = pivot.sort_index(ascending=False)
    last_2_months = pivot.head(2)
    st.dataframe(last_2_months)

    # Full history in single expander
    with st.expander("Show Full History"):
        st.dataframe(pivot)
else:
    st.info("No data available yet")

# ---------- RESET DATABASE BUTTON AT BOTTOM ---------- #
if st.session_state.get("admin", False):
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("⚠️ Reset Database (Start Fresh)"):
        reset_db()
        st.warning("Database reset! Reload the page to start first-time setup.")







