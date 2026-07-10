import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
from streamlit_geolocation import streamlit_geolocation

# --- CONFIG ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwBbxweh9uGtzQLoKrqi6F9VKuYwRJU4lp6y-bYQD5597tYx6ylTn7LRbj5EM0cujh3/exec"
dubai_tz = pytz.timezone("Asia/Dubai")

st.title("📍 Employee Attendance Portal")

# 1. جلب الأسماء من جوجل شيت
try:
    response = requests.get(WEB_APP_URL)
    data = response.json()
    # تحويل البيانات لـ DataFrame (بافتراض الصف الأول هو العناوين)
    df_emp = pd.DataFrame(data[1:], columns=data[0])
    employee_names = df_emp['Name'].tolist()
except:
    st.error("Cannot load employees. Check your Google Script link.")
    employee_names = []

# 2. اختيار الاسم من قائمة
selected_name = st.selectbox("Select Your Name", [None] + employee_names)

if selected_name:
    loc = streamlit_geolocation()
    if loc and loc.get('latitude'):
        img = st.camera_input("Capture Attendance")
        if img:
            now = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
            # إرسال البيانات
            payload = {"name": selected_name, "time": now, "type": "Check", "lat": loc['latitude'], "lon": loc['longitude']}
            response = requests.post(WEB_APP_URL, json=payload)
            if response.status_code == 200:
                st.success("✅ Attendance Recorded!")
            else:
                st.error("Failed to connect to database.")
