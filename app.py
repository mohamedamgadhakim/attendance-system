import streamlit as st
import sqlite3
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime
import pytz
from geopy.distance import geodesic

# Setup
dubai_tz = pytz.timezone("Asia/Dubai")
conn = sqlite3.connect('attendance_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS employees (name TEXT PRIMARY KEY, lat REAL, lon REAL, radius REAL)')
c.execute('CREATE TABLE IF NOT EXISTS logs (name TEXT, time TEXT, action TEXT)')
conn.commit()

st.title("Attendance System - Dubai")

# Admin Dashboard
with st.expander("Admin Panel"):
    if st.text_input("Password", type="password") == "1234":
        name_in = st.text_input("New Employee Name")
        lat_in = st.number_input("Lat", format="%.6f")
        lon_in = st.number_input("Lon", format="%.6f")
        rad_in = st.number_input("Radius (meters)", value=200.0)
        if st.button("Add Employee"):
            c.execute("REPLACE INTO employees VALUES (?,?,?,?)", (name_in, lat_in, lon_in, rad_in))
            conn.commit()
            st.success("Employee added.")
        st.dataframe(pd.read_sql("SELECT * FROM employees", conn))

# Employee Workflow
emp_names = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
selected_name = st.selectbox("Select your name", emp_names)

if selected_name:
    loc = streamlit_geolocation()
    if loc and loc['latitude']:
        emp_data = c.execute("SELECT lat, lon, radius FROM employees WHERE name=?", (selected_name,)).fetchone()
        dist = geodesic((loc['latitude'], loc['longitude']), (emp_data[0], emp_data[1])).meters
        
        if dist <= emp_data[2]:
            st.success("Location Verified!")
            img = st.camera_input("Take your photo")
            if img:
                col1, col2 = st.columns(2)
                if col1.button("Check-in"):
                    c.execute("INSERT INTO logs VALUES (?, ?, ?)", (selected_name, datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S"), "Check-in"))
                    conn.commit()
                    st.success("Check-in recorded!")
                if col2.button("Check-out"):
                    c.execute("INSERT INTO logs VALUES (?, ?, ?)", (selected_name, datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S"), "Check-out"))
                    conn.commit()
                    st.success("Check-out recorded!")
        else:
            st.error(f"You are out of range! Distance: {int(dist)}m")
    else:
        st.info("Checking location...")