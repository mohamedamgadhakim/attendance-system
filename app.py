import streamlit as st
import pandas as pd
import requests, base64
from datetime import datetime
import pytz
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwWNmDtToXAbWq9CGEBsU41ndXd3QE0GXM_uzNVeKIjERrh8I0i4Uj0C4f8SMrUAhk/exec"
dubai_tz = pytz.timezone("Asia/Dubai")

st.title("📍 Attendance System")

# جلب الأسماء
try:
    data = requests.get(WEB_APP_URL).json()
    df_emp = pd.DataFrame(data[1:], columns=data[0])
except: st.error("Database connection error"); st.stop()

selected_name = st.selectbox("Select Name", [None] + df_emp['Name'].tolist())

if selected_name:
    emp_info = df_emp[df_emp['Name'] == selected_name].iloc[0]
    loc = streamlit_geolocation()
    
    if loc and loc.get('latitude'):
        dist = geodesic((loc['latitude'], loc['longitude']), (float(emp_info['Lat']), float(emp_info['Lon']))).meters
        
        if dist <= float(emp_info['Radius']):
            img = st.camera_input("Capture Attendance")
            if img:
                b64_img = base64.b64encode(img.getvalue()).decode()
                now = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
                
                c1, c2 = st.columns(2)
                if c1.button("Check-in"):
                    requests.post(WEB_APP_URL, json={"name": selected_name, "time": now, "type": "In", "lat": loc['latitude'], "lon": loc['longitude'], "photo": b64_img})
                    st.success("Check-in Recorded!")
                if c2.button("Check-out"):
                    requests.post(WEB_APP_URL, json={"name": selected_name, "time": now, "type": "Out", "lat": loc['latitude'], "lon": loc['longitude'], "photo": b64_img})
                    st.success("Check-out Recorded!")
        else:
            st.error(f"❌ Out of range! ({int(dist)}m)")
