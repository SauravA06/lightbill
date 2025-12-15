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

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Electricity Bill Dashboard", layout="wide")

# ---------- TOP ----------
st.markdown("<h1 style='text-align:center;'>⚡ Electricity Bill Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ---------- INIT DB ----------
init_db()

# ---------- PASSWORD SECTION ----------
st.markdown("<h4 style='text-align:center;'>Enter Admin Password</h4>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    password = st.text_input("", type="password", placeholder="Password")
    login_clicked = st.button("Login", use_container_width=True)

if login_clicked:
    if password == st.secrets["ADMIN_PASSWORD"]:
        st.session_state["admin"] = True
        st.success("✅ Admin Access Granted")
    else:
        st.error("❌ Incorrect password")

# ---------- ADMIN AREA ----------
if st.session_state.get("admin", False):

    # ---------- MONTH & YEAR SELECTOR ----------
    def select_month_year(label, key):
        st.subheader(label)
        c1, c2 = st.columns(2)

        with c1:
            month = st.selectbox(
                "Month",
                ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
                index=datetime.now().month - 1,
                key=f"{key}_month"
            )

        with c2:
            year = st.number_input(
                "Year",
                min_value=2000,
                max_value=2100,
                value=datetime.now().year,
                step=1,
                key=f"{key}_year"
            )

        return f"{month}-{year}"

    # ---------- FIRST TIME SETUP ----------
    if not is_initialized():
        st.warning("First-time setup: Enter initial readings")
        init_month = select_month_year("Initial Readings Month", "init")

        t1 = st.number_input("Tenant 1 Initial Reading", min_value=0)
        t2 = st.number_input("Tenant 2 Initial Reading", min_value=0)
        t3 = st.number_input("Tenant 3 Initial Reading", min_value=0)
        water = st.number_input("Water Motor Initial Reading", min_value=0)

        if st.button("Save Initial Readings"):
            update_readings(
                {"t1": t1, "t2": t2, "t3": t3, "water": water},
                month=init_month
            )
            st.success("Initial readings saved. Reload page.")
            st.stop()

    st.success("Previous month readings loaded automatically")

    # ---------- CURRENT READINGS ----------
    prev = {k: get_previous_reading(k) for k in ["t1", "t2", "t3", "water"]}
    month_str = select_month_year("Current Month Readings", "current")

    st.subheader("Enter Current Readings")
    current = {
        "t1": st.number_input("Tenant 1", min_value=prev["t1"]),
        "t2": st.number_input("Tenant 2", min_value=prev["t2"]),
        "t3": st.number_input("Tenant 3", min_value=prev["t3"]),
        "water": st.number_input("Water Motor", min_value=prev["water"]),
    }

    st.subheader("Optional: Actual Bill Paid (₹)")
    actual_bill = st.number_input("Amount Paid to MSEDCL", min_value=0, value=0)

    bills = None

    if st.button("Calculate Bill"):
        bills = (
            calculate_bill(current, actual_total_bill=actual_bill)
            if actual_bill > 0
            else calculate_bill(current)
        )

    # ---------- DISPLAY TENANT CARDS ----------
    if bills:

        tenant_keys = ["t1", "t2", "t3"]

        amounts_sorted = sorted(
            [(k, bills[k]["amount"]) for k in tenant_keys],
            key=lambda x: x[1]
        )

        COLOR_THEME = {
            "green": {"bg": "#E8F5E9", "text": "#1B5E20"},
            "yellow": {"bg": "#FFF8E1", "text": "#6D4C00"},
            "red": {"bg": "#FDECEA", "text": "#7F1D1D"},
        }

        rank_color = {
            amounts_sorted[0][0]: "green",
            amounts_sorted[1][0]: "yellow",
            amounts_sorted[2][0]: "red",
        }

        st.subheader("Final Bill Distribution")

        cols = st.columns(3)
        amounts_to_save = {}

        for col, tenant in zip(cols, tenant_keys):
            theme = COLOR_THEME[rank_color[tenant]]

            with col:
                st.markdown(
                    f"""
                    <div style="
                        background:{theme['bg']};
                        padding:18px;
                        border-radius:12px;
                        border-left:6px solid {theme['text']};
                    ">
                        <h4 style="color:{theme['text']};">Tenant {tenant[-1]}</h4>
                        <p style="color:{theme['text']};">Units: <b>{bills[tenant]['units']}</b></p>
                        <p style="color:{theme['text']};">Amount: <b>₹{bills[tenant]['amount']}</b></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                amounts_to_save[tenant] = bills[tenant]["amount"]

        update_readings(current, month_str, amounts=amounts_to_save)
        st.success("Readings saved successfully ✅")

# ---------- HISTORY ----------
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("📊 Last 2 Months Summary")

history = get_full_history()
if history:
    df = pd.DataFrame(history, columns=["Meter", "Month", "Reading", "Amount"])
    pivot = df.pivot_table(
        index="Month",
        columns="Meter",
        values=["Reading", "Amount"],
        aggfunc="first"
    ).sort_index(ascending=False)

    for col in pivot.columns:
        if col[0] == "Amount":
            pivot[col] = pivot[col].apply(lambda x: f"₹{x}" if pd.notnull(x) else "")

    st.dataframe(pivot.head(2), use_container_width=True)

    with st.expander("Show Full History"):
        st.dataframe(pivot, use_container_width=True)
else:
    st.info("No history available yet")

# ---------- RESET DB ----------
if st.session_state.get("admin", False):
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("⚠️ Reset Database"):
        reset_db()
        st.warning("Database reset. Reload page.")
