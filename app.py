import streamlit as st
import pandas as pd
import requests, base64
from datetime import datetime
import pytz
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxpsf22erhQ4EV1E7OO0A3oXV_Kdq5pVhfmQFgZUW46xU5-A0WuZxCqJYV3wd2MjQek/exec"
dubai_tz = pytz.timezone("Asia/Dubai")

st.title("Attendance System")

# Fetch Employee Data
try:
    response = requests.get(WEB_APP_URL)
    data = response.json()
    df_emp = pd.DataFrame(data[1:], columns=data[0])
except:
    st.error("Error connecting to database!")
    st.stop()

selected_name = st.selectbox("Select Your Name", [None] + df_emp['Name'].tolist())

if selected_name:
    # Get specific employee info
    emp_info = df_emp[df_emp['Name'] == selected_name].iloc[0]
    
    st.info("Verifying your location...")
    loc = streamlit_geolocation()
    
    if loc and loc.get('latitude'):
        # Precise distance calculation
        emp_lat = float(emp_info['Lat'])
        emp_lon = float(emp_info['Lon'])
        radius = float(emp_info['Radius'])
        
        dist = geodesic((loc['latitude'], loc['longitude']), (emp_lat, emp_lon)).meters
        st.write(f"Distance to Office: {int(dist)} meters")
        
        # Location Validation Logic
        if dist <= radius:
            st.success("Location Verified!")
            img = st.camera_input("Take Attendance Photo")
            
            if img:
                b64_img = base64.b64encode(img.getvalue()).decode()
                now = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
                
                c1, c2 = st.columns(2)
                
                # Check-in button
                if c1.button("Check-in", disabled=st.session_state.get('loading', False)):
                    st.session_state['loading'] = True
                    requests.post(WEB_APP_URL, json={"name": selected_name, "time": now, "type": "In", "lat": loc['latitude'], "lon": loc['longitude'], "photo": b64_img})
                    st.success("Check-in recorded!")
                    st.rerun()
                
                # Check-out button
                if c2.button("Check-out", disabled=st.session_state.get('loading', False)):
                    st.session_state['loading'] = True
                    requests.post(WEB_APP_URL, json={"name": selected_name, "time": now, "type": "Out", "lat": loc['latitude'], "lon": loc['longitude'], "photo": b64_img})
                    st.success("Check-out recorded!")
                    st.rerun()
        else:
            st.error(f"Access Denied! You are {int(dist)}m away. Allowed radius: {int(radius)}m.")
