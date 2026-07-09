import streamlit as st
import sqlite3
import pandas as pd
import base64
from datetime import datetime, timedelta
import pytz
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

# --- CONFIG ---
st.set_page_config(page_title="Attendance Pro", layout="wide")
dubai_tz = pytz.timezone("Asia/Dubai")
conn = sqlite3.connect('attendance_pro_v3.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS employees (name TEXT, lat REAL, lon REAL, radius REAL, salary REAL)')
c.execute('CREATE TABLE IF NOT EXISTS logs (name TEXT, time TEXT, type TEXT, lat REAL, lon REAL, photo TEXT)')
conn.commit()

# --- ADMIN PANEL ---
with st.sidebar:
    st.header("Admin Control")
    if st.text_input("Admin Password", type="password") == "1234":
        st.subheader("Monthly Reports")
        
        # 1. تنظيف البيانات (الاحتفاظ بآخر شهرين فقط)
        if st.button("Cleanup Old Data (Keep last 2 months)"):
            two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("DELETE FROM logs WHERE time < ?", (two_months_ago,))
            conn.commit()
            st.success("Old data cleaned!")

        # 2. فلترة وتصدير حسب الشهر
        df = pd.read_sql("SELECT * FROM logs", conn)
        df['time'] = pd.to_datetime(df['time'])
        df['month'] = df['time'].dt.strftime('%Y-%m')
        
        selected_month = st.selectbox("Select Month to Export", sorted(df['month'].unique(), reverse=True))
        filtered_df = df[df['month'] == selected_month]
        
        if st.button("Export Selected Month"):
            html = f"<html><body><h1>Report for {selected_month}</h1><table border='1'><tr><th>Name</th><th>Time</th><th>Action</th><th>Photo</th></tr>"
            for _, row in filtered_df.iterrows():
                img_tag = f"<img src='data:image/png;base64,{row['photo']}' width='60'>" if row['photo'] else "No Photo"
                html += f"<tr><td>{row['name']}</td><td>{row['time']}</td><td>{row['type']}</td><td>{img_tag}</td></tr>"
            html += "</table></body></html>"
            st.download_button("Download Report", html, f"report_{selected_month}.html", "text/html")

        # 3. إدارة الموظفين
        with st.expander("Manage Employees"):
            name = st.text_input("Name")
            lat, lon = st.number_input("Lat", format="%.6f"), st.number_input("Lon", format="%.6f")
            if st.button("Save"):
                c.execute("INSERT INTO employees VALUES (?,?,?,?,?)", (name, lat, lon, 200.0, 3000))
                conn.commit()

# --- EMPLOYEE PORTAL ---
st.title("📍 Employee Attendance Portal")
emp_names = list(set([r[0] for r in c.execute("SELECT name FROM employees").fetchall()]))
selected_name = st.selectbox("Select Your Name", [None] + emp_names)

if selected_name:
    st.info("Verifying location...")
    loc = streamlit_geolocation()
    if loc and loc.get('latitude'):
        allowed = c.execute("SELECT lat, lon, radius FROM employees WHERE name=?", (selected_name,)).fetchall()
        in_range = any([geodesic((loc['latitude'], loc['longitude']), (l[0], l[1])).meters <= l[2] for l in allowed])
        
        with st.container(border=True):
            if in_range:
                img = st.camera_input("Capture Attendance")
                if img:
                    b64_img = base64.b64encode(img.getvalue()).decode()
                    now_str = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
                    col1, col2 = st.columns(2)
                    if col1.button("Check-in 📥"):
                        c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now_str, "In", loc['latitude'], loc['longitude'], b64_img))
                        conn.commit()
                        st.toast("Check-in recorded!")
                    if col2.button("Check-out 📤"):
                        c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now_str, "Out", loc['latitude'], loc['longitude'], b64_img))
                        conn.commit()
                        st.toast("Check-out recorded!")
            else:
                st.error("❌ Access Denied: You are outside the authorized area.")
