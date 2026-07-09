import streamlit as st
import sqlite3
import pandas as pd
import base64
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime
import pytz
from geopy.distance import geodesic

# --- CONFIG ---
st.set_page_config(page_title="Pro Attendance System", layout="wide")
dubai_tz = pytz.timezone("Asia/Dubai")
conn = sqlite3.connect('attendance_final.db', check_same_thread=False)
c = conn.cursor()

# Initialize Tables
c.execute('CREATE TABLE IF NOT EXISTS employees (name TEXT, lat REAL, lon REAL, radius REAL, salary REAL)')
c.execute('CREATE TABLE IF NOT EXISTS logs (name TEXT, time TEXT, type TEXT, lat REAL, lon REAL, photo TEXT)')
conn.commit()

# --- ADMIN PANEL ---
with st.sidebar:
    st.header("Admin Panel")
    if st.text_input("Admin Password", type="password") == "1234":
        st.subheader("Manage Employees")
        name = st.text_input("Emp Name")
        lat, lon = st.number_input("Lat", format="%.6f"), st.number_input("Lon", format="%.6f")
        rad = st.number_input("Radius (meters)", value=200.0)
        sal = st.number_input("Salary", value=3000.0)
        if st.button("Add/Update Location"):
            c.execute("INSERT INTO employees VALUES (?,?,?,?,?)", (name, lat, lon, rad, sal))
            conn.commit()
            st.success("Location Added!")

        st.subheader("Attendance Logs")
        df = pd.read_sql("SELECT * FROM logs", conn)
        for index, row in df.iterrows():
            st.write(f"**{row['name']}** | {row['time']} | {row['type']}")
            if row['photo']:
                st.image(base64.b64decode(row['photo']), width=150)
            st.divider()

# --- EMPLOYEE PORTAL ---
st.title("Employee Attendance System")
emp_names = list(set([r[0] for r in c.execute("SELECT name FROM employees").fetchall()]))
selected_name = st.selectbox("Select Your Name", emp_names)

if selected_name:
    loc = streamlit_geolocation()
    if loc and loc['latitude']:
        allowed = c.execute("SELECT lat, lon, radius FROM employees WHERE name=?", (selected_name,)).fetchall()
        in_range = any([geodesic((loc['latitude'], loc['longitude']), (l[0], l[1])).meters <= l[2] for l in allowed])
        
        if in_range:
            st.success("Verified: In Authorized Zone")
            img = st.camera_input("Take Attendance Photo")
            if img:
                b64_img = base64.b64encode(img.getvalue()).decode()
                now_str = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
                
                col1, col2 = st.columns(2)
                if col1.button("Check-in"):
                    c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now_str, "In", loc['latitude'], loc['longitude'], b64_img))
                    conn.commit()
                    st.toast("Check-in Recorded!")
                if col2.button("Check-out"):
                    c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now_str, "Out", loc['latitude'], loc['longitude'], b64_img))
                    conn.commit()
                    st.toast("Check-out Recorded!")
        else:
            st.error("Error: You are outside the authorized area.")
