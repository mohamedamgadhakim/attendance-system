import streamlit as st
import sqlite3
import pandas as pd
import base64
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime
import pytz
from geopy.distance import geodesic

st.set_page_config(page_title="Pro Attendance System", layout="wide")
dubai_tz = pytz.timezone("Asia/Dubai")
conn = sqlite3.connect('attendance_pro_v3.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS employees (name TEXT, lat REAL, lon REAL, radius REAL, salary REAL)')
c.execute('CREATE TABLE IF NOT EXISTS logs (name TEXT, time TEXT, type TEXT, lat REAL, lon REAL, photo TEXT)')
conn.commit()

# --- ADMIN PANEL ---
with st.sidebar:
    st.header("Admin Panel")
    if st.text_input("Admin Password", type="password") == "1234":
        
        # تصدير تقرير احترافي (HTML)
        st.subheader("Professional Export")
        df = pd.read_sql("SELECT * FROM logs", conn)
        
        html_content = "<html><body><h1>Attendance Report</h1><table border='1'><tr><th>Name</th><th>Time</th><th>Action</th><th>Photo</th></tr>"
        for _, row in df.iterrows():
            img_tag = f"<img src='data:image/png;base64,{row['photo']}' width='100'>" if row['photo'] else "No Photo"
            html_content += f"<tr><td>{row['name']}</td><td>{row['time']}</td><td>{row['type']}</td><td>{img_tag}</td></tr>"
        html_content += "</table></body></html>"
        
        st.download_button("Download Report as Excel/HTML", html_content, "attendance_report.html", "text/html")
        
        st.divider()
        # إضافة موظفين
        with st.expander("➕ Add Employee"):
            name = st.text_input("Emp Name")
            lat, lon = st.number_input("Lat", format="%.6f"), st.number_input("Lon", format="%.6f")
            rad = st.number_input("Radius", value=200.0)
            if st.button("Save"):
                c.execute("INSERT INTO employees VALUES (?,?,?,?,?)", (name, lat, lon, rad, 3000))
                conn.commit()
                st.success("Added!")

# --- EMPLOYEE PORTAL ---
st.title("Employee Attendance")
emp_names = list(set([r[0] for r in c.execute("SELECT name FROM employees").fetchall()]))
selected_name = st.selectbox("Select Your Name", emp_names)

if selected_name:
    loc = streamlit_geolocation()
    if loc and loc['latitude']:
        allowed = c.execute("SELECT lat, lon, radius FROM employees WHERE name=?", (selected_name,)).fetchall()
        if any([geodesic((loc['latitude'], loc['longitude']), (l[0], l[1])).meters <= l[2] for l in allowed]):
            img = st.camera_input("Verify Identity")
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
