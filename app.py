import streamlit as st
import sqlite3
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime, time
import pytz
from geopy.distance import geodesic

# 1. إعداد التوقيت وقاعدة البيانات
dubai_tz = pytz.timezone("Asia/Dubai")
conn = sqlite3.connect('attendance_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS employees 
             (name TEXT PRIMARY KEY, lat REAL, lon REAL, radius REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (name TEXT, time TEXT, action TEXT)''')
conn.commit()

# تهيئة الموظفين (إذا لم يكونوا موجودين)
for emp in [("Mohamed", 25.250074, 55.337146, 200), ("Ahmed", 25.262200, 55.387334, 200)]:
    c.execute("INSERT OR IGNORE INTO employees VALUES (?,?,?,?)", emp)
conn.commit()

st.title("Attendance & Payroll System - Dubai")

# 2. لوحة الإدارة
with st.expander("Admin Dashboard"):
    admin_pass = st.text_input("Admin Password", type="password")
    if admin_pass == "1234":
        st.write("Current Logs:")
        df = pd.read_sql("SELECT * FROM logs", conn)
        st.dataframe(df)
        st.download_button("Download Report (CSV)", df.to_csv(), "attendance_report.csv")

# 3. واجهة الموظف
selected_name = st.selectbox("Select your name", ["Mohamed", "Ahmed"])
loc = streamlit_geolocation()

if loc and loc['latitude']:
    if st.button("Submit Action (Check-in/Out)"):
        emp_data = c.execute("SELECT lat, lon, radius FROM employees WHERE name=?", (selected_name,)).fetchone()
        dist = geodesic((loc['latitude'], loc['longitude']), (emp_data[0], emp_data[1])).meters
        
        if dist <= emp_data[2]:
            # الحصول على التوقيت بدقة في دبي
            now = datetime.now(dubai_tz)
            
            # منطق الحضور (القواعد)
            status = "On Time"
            if now.time() > time(9, 10):
                status = "LATE - Deduction Applied"
            
            c.execute("INSERT INTO logs VALUES (?, ?, ?)", (selected_name, now.strftime("%Y-%m-%d %H:%M:%S"), status))
            conn.commit()
            st.success(f"Successfully recorded: {status}")
        else:
            st.error(f"Access Denied: You are {int(dist)}m away from the site.")