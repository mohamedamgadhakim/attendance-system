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
dubai_tz = pytz.timezone("Dubai")
conn = sqlite3.connect('attendance_pro_v3.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS employees (name TEXT PRIMARY KEY, lat REAL, lon REAL, radius REAL, salary REAL)')
c.execute('CREATE TABLE IF NOT EXISTS logs (name TEXT, time TEXT, type TEXT, lat REAL, lon REAL, photo TEXT)')
conn.commit()

# --- ADMIN PANEL ---
with st.sidebar:
    st.header("Admin Control")
    if st.text_input("Admin Password", type="password") == "1234":
        
        # 1. ADD NEW EMPLOYEE
        with st.expander("➕ Add New Employee"):
            new_name = st.text_input("Full Name")
            new_lat = st.number_input("Latitude", format="%.6f")
            new_lon = st.number_input("Longitude", format="%.6f")
            new_rad = st.number_input("Radius (meters)", value=200.0)
            new_sal = st.number_input("Monthly Salary", value=3000.0)
            if st.button("Register Employee"):
                try:
                    c.execute("INSERT INTO employees VALUES (?,?,?,?,?)", (new_name, new_lat, new_lon, new_rad, new_sal))
                    conn.commit()
                    st.success(f"{new_name} registered!")
                except:
                    st.error("Employee already exists.")

        # 2. EDIT/DELETE EMPLOYEE
        with st.expander("✏️ Edit / Delete Employee"):
            emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
            target_name = st.selectbox("Select Employee", emp_list)
            if target_name:
                data = c.execute("SELECT * FROM employees WHERE name=?", (target_name,)).fetchone()
                e_lat = st.number_input("Edit Lat", value=data[1], format="%.6f")
                e_lon = st.number_input("Edit Lon", value=data[2], format="%.6f")
                e_rad = st.number_input("Edit Radius (m)", value=data[3])
                e_sal = st.number_input("Edit Salary", value=data[4])
                
                col_e, col_d = st.columns(2)
                if col_e.button("Update Details"):
                    c.execute("UPDATE employees SET lat=?, lon=?, radius=?, salary=? WHERE name=?", (e_lat, e_lon, e_rad, e_sal, target_name))
                    conn.commit()
                    st.success("Updated successfully!")
                
                if col_d.button("🗑️ Delete Employee"):
                    c.execute("DELETE FROM employees WHERE name=?", (target_name,))
                    conn.commit()
                    st.warning(f"{target_name} has been deleted.")
                    st.rerun()

        # 3. REPORTS
        st.subheader("Monthly Reports")
        if st.button("Cleanup Old Data (> 60 days)"):
            c.execute("DELETE FROM logs WHERE time < ?", ((datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S"),))
            conn.commit()
        
        df = pd.read_sql("SELECT * FROM logs", conn)
        df['time'] = pd.to_datetime(df['time'])
        df['month'] = df['time'].dt.strftime('%Y-%m')
        selected_month = st.selectbox("Select Month", sorted(df['month'].unique(), reverse=True))
        
        if st.button("Export Selected Month"):
            filtered_df = df[df['month'] == selected_month].sort_values(['name', 'type', 'time'])
            html = "<html><body><h1>Report</h1><table border='1'><tr><th>Name</th><th>Time</th><th>Action</th><th>Photo</th></tr>"
            for _, row in filtered_df.iterrows():
                img_tag = f"<img src='data:image/png;base64,{row['photo']}' width='60'>" if row['photo'] else "No Photo"
                html += f"<tr><td>{row['name']}</td><td>{row['time']}</td><td>{row['type']}</td><td>{img_tag}</td></tr>"
            html += "</table></body></html>"
            st.download_button("Download Report", html, f"report_{selected_month}.html", "text/html")

# --- EMPLOYEE PORTAL ---
st.title("📍 Employee Attendance Portal")
emp_names = list(set([r[0] for r in c.execute("SELECT name FROM employees").fetchall()]))
selected_name = st.selectbox("Select Your Name", [None] + emp_names)

if selected_name:
    st.info("Verifying location...")
    loc = streamlit_geolocation()
    if loc and loc.get('latitude'):
        emp_data = c.execute("SELECT lat, lon, radius FROM employees WHERE name=?", (selected_name,)).fetchone()
        in_range = geodesic((loc['latitude'], loc['longitude']), (emp_data[0], emp_data[1])).meters <= emp_data[2]
        
        with st.container(border=True):
            if in_range:
                img = st.camera_input("Capture Attendance")
                if img:
                    b64_img = base64.b64encode(img.getvalue()).decode()
                    now = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
                    c1, c2 = st.columns(2)
                    if c1.button("Check-in 📥"):
                        c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now, "In", loc['latitude'], loc['longitude'], b64_img))
                        conn.commit()
                        st.toast("Check-in recorded!")
                    if c2.button("Check-out 📤"):
                        c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (selected_name, now, "Out", loc['latitude'], loc['longitude'], b64_img))
                        conn.commit()
                        st.toast("Check-out recorded!")
            else:
                st.error("❌ Access Denied: You are outside the authorized area.")
