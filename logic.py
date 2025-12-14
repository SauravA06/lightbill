import sqlite3

DB_NAME = "electricity.db"
COST_PER_UNIT = 10  # ₹10 per unit


# ---------- DATABASE SETUP ---------- #
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meters (
            meter_id TEXT PRIMARY KEY,
            last_reading INTEGER
        )
    """)
    meters = [
        ('t1', 0),
        ('t2', 0),
        ('t3', 0),
        ('water', 0)
    ]
    cur.executemany("INSERT OR IGNORE INTO meters VALUES (?, ?)", meters)
    conn.commit()
    conn.close()


# ---------- DATABASE OPERATIONS ---------- #
def get_previous_reading(meter_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT last_reading FROM meters WHERE meter_id=?", (meter_id,))
    value = cur.fetchone()[0]
    conn.close()
    return value


def update_readings(readings: dict):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for meter_id, value in readings.items():
        cur.execute(
            "UPDATE meters SET last_reading=? WHERE meter_id=?",
            (value, meter_id)
        )
    conn.commit()
    conn.close()


# ---------- BILL CALCULATION ---------- #
def calculate_bill(current_readings: dict):
    prev = {m: get_previous_reading(m) for m in current_readings}

    tenant_units = {
        m: current_readings[m] - prev[m]
        for m in ['t1', 't2', 't3']
    }

    water_units = current_readings['water'] - prev['water']
    water_share = water_units / 3

    final_units = {
        m: tenant_units[m] + water_share
        for m in tenant_units
    }

    bills = {
        m: {
            "units": round(final_units[m], 2),
            "amount": round(final_units[m] * COST_PER_UNIT, 2)
        }
        for m in final_units
    }

    return bills

def is_initialized():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM meters WHERE last_reading > 0")
    count = cur.fetchone()[0]
    conn.close()

    return count > 0

def is_initialized():
    """
    Returns True if at least one meter has a non-zero reading.
    Used to check if initial readings have been set.
    """
    import sqlite3
    DB_NAME = "electricity.db"
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM meters WHERE last_reading > 0")
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


