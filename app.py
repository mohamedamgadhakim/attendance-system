import streamlit as st
import sqlite3
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime
from geopy.distance import geodesic

# Setup Database
conn = sqlite3.connect('attendance.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS employees 
             (name TEXT PRIMARY KEY, lat REAL, lon REAL, salary REAL, 
              work_days TEXT, shift_start TEXT, shift_end TEXT, paid_leave REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (name TEXT, time TEXT, action TEXT, lat REAL, lon REAL)''')
conn.commit()

st.title("Attendance & Payroll System")

# Admin Dashboard
with st.expander("Admin Control Panel"):
    admin_pass = st.text_input("Admin Password", type="password")
    if admin_pass == "1234":
        tab1, tab2, tab3 = st.tabs(["Add/Update Employee", "Delete Employee", "Attendance Logs"])
        
        with tab1:
            name = st.text_input("Employee Name")
            lat = st.number_input("Allowed Latitude", format="%.6f")
            lon = st.number_input("Allowed Longitude", format="%.6f")
            salary = st.number_input("Monthly Salary")
            work_days = st.text_input("Work Days (e.g., Sat-Thu)")
            paid_leave = st.number_input("Paid Leaves Allowed")
            if st.button("Save/Update Employee"):
                c.execute("REPLACE INTO employees VALUES (?,?,?,?,?,?,?,?)", 
                          (name, lat, lon, salary, work_days, "09:00", "17:00", paid_leave))
                conn.commit()
                st.success("Employee saved.")

        with tab2:
            del_name = st.selectbox("Select employee to delete", [r[0] for r in c.execute("SELECT name FROM employees").fetchall()])
            if st.button("Delete Employee"):
                c.execute("DELETE FROM employees WHERE name=?", (del_name,))
                conn.commit()
                st.success("Employee deleted.")

        with tab3:
            df = pd.read_sql("SELECT * FROM logs", conn)
            st.dataframe(df)
            st.download_button("Export to CSV", df.to_csv(), "attendance_log.csv")

# Employee Interface
st.subheader("Mark Attendance")
emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
selected_name = st.selectbox("Select your name", emp_list)

loc = streamlit_geolocation()

if loc and loc['latitude']:
    img = st.camera_input("Take a photo")
    if img and st.button("Submit Attendance"):
        # Fetch target coordinates
        emp_data = c.execute("SELECT lat, lon FROM employees WHERE name=?", (selected_name,)).fetchone()
        
        # Geofencing Logic: Calculating distance in meters
        target_loc = (emp_data[0], emp_data[1])
        current_loc = (loc['latitude'], loc['longitude'])
        dist = geodesic(current_loc, target_loc).meters
        
        # Strict validation
        if dist <= 150: # 150 meters tolerance
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO logs VALUES (?, ?, ?, ?, ?)", 
                      (selected_name, now, "Check-in/out", loc['latitude'], loc['longitude']))
            conn.commit()
            st.success(f"Attendance recorded successfully! Distance: {int(dist)}m")
        else:
            st.error(f"Access Denied! You are {int(dist)}m away from the authorized location.")
else:
    st.info("Please enable Location in your browser to proceed.")