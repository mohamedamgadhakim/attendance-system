import streamlit as st
import sqlite3
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime
import pytz
from geopy.distance import geodesic

# Setup
dubai_tz = pytz.timezone("Asia/Dubai")
conn = sqlite3.connect('attendance_pro.db', check_same_thread=False)
c = conn.cursor()

# Tables Setup
c.execute('''CREATE TABLE IF NOT EXISTS employees 
             (name TEXT PRIMARY KEY, lat REAL, lon REAL, radius REAL, salary REAL, work_days TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (name TEXT, time TEXT, type TEXT, lat REAL, lon REAL, photo_taken TEXT)''')
conn.commit()

st.title("Attendance & Payroll Pro System")

# Admin Dashboard
with st.expander("Admin Control Panel"):
    if st.text_input("Admin Password", type="password") == "1234":
        tab1, tab2 = st.tabs(["Manage Employees", "Reports & Payroll"])
        with tab1:
            name = st.text_input("Name")
            lat, lon = st.number_input("Lat", format="%.6f"), st.number_input("Lon", format="%.6f")
            rad = st.number_input("Radius", value=200.0)
            sal = st.number_input("Monthly Salary")
            days = st.text_input("Work Days (e.g., Mon-Sat)")
            if st.button("Add/Update Employee"):
                c.execute("REPLACE INTO employees VALUES (?,?,?,?,?,?)", (name, lat, lon, rad, sal, days))
                conn.commit()
                st.success("Employee updated.")
        with tab2:
            df = pd.read_sql("SELECT * FROM logs", conn)
            st.dataframe(df)
            # Payroll Logic: Deductions
            if st.button("Calculate Salaries"):
                # Logic: 9:10 threshold
                df['time'] = pd.to_datetime(df['time'])
                late_count = df[df['time'].dt.hour >= 9].shape[0] # Example Logic
                st.write(f"Total Late Entries Detected: {late_count}")
                st.download_button("Export Full Report", df.to_csv(), "Payroll_Report.csv")

# Employee Workflow
emp_names = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
selected_name = st.selectbox("Select Name", emp_names)

if selected_name:
    loc = streamlit_geolocation()
    if loc and loc['latitude']:
        emp = c.execute("SELECT lat, lon, radius FROM employees WHERE name=?", (selected_name,)).fetchone()
        if geodesic((loc['latitude'], loc['longitude']), (emp[0], emp[1])).meters <= emp[2]:
            st.success("Verified: In Location")
            img = st.camera_input("Take Photo for Attendance")
            if img:
                col1, col2 = st.columns(2)
                now_str = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
                if col1.button("Check-in"):
                    c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now_str, "In", loc['latitude'], loc['longitude'], "Yes"))
                    conn.commit()
                if col2.button("Check-out"):
                    c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now_str, "Out", loc['latitude'], loc['longitude'], "Yes"))
                    conn.commit()
        else:
            st.error("Access Denied: You are outside the allowed radius.")