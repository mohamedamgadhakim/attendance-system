import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import pytz
from streamlit_geolocation import streamlit_geolocation

# --- CONFIG ---
st.set_page_config(page_title="Attendance Pro", layout="wide")
dubai_tz = pytz.timezone("Asia/Dubai")
# الرابط الذي حصلت عليه من الـ Web App
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwoOSIMF1Od46KOFTMD97d47v6op6bg5b1gUf1ypnfGJMxbdxjvVCrvGW0-aFnc5vxv/exec"

# --- EMPLOYEE PORTAL ---
st.title("📍 Employee Attendance Portal")

# قراءة بيانات الموظفين من جوجل شيت (يجب أن يكون الشيت متاحاً للقراءة العامة)
# ملاحظة: في المرة القادمة سأعلمك كيف تجعل الشيت يقرأ البيانات بسهولة، 
# لكن حالياً سنركز على تسجيل الحضور
selected_name = st.text_input("Enter Your Name") # مؤقتاً لحين ربط قراءة الشيت

if selected_name:
    st.info("Verifying location...")
    loc = streamlit_geolocation()
    if loc and loc.get('latitude'):
        # هنا سيقوم النظام بالتحقق من الموقع ثم إرسال البيانات للرابط
        img = st.camera_input("Capture Attendance")
        if img:
            import base64
            b64_img = base64.b64encode(img.getvalue()).decode()
            now = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            payload = {
                "name": selected_name,
                "time": now,
                "type": "Check",
                "lat": loc['latitude'],
                "lon": loc['longitude'],
                "photo": "Image Captured" # يمكنك إرسال الـ b64_img هنا إذا كانت الصورة صغيرة
            }
            
            # إرسال البيانات لجوجل شيت
            response = requests.post(WEB_APP_URL, json=payload)
            if response.status_code == 200:
                st.success("✅ Attendance Recorded Successfully in Google Sheets!")
            else:
                st.error("Failed to connect to database.")
