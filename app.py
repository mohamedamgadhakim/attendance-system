import streamlit as st
import pandas as pd
import requests
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation
import base64
from datetime import datetime
import pytz

# --- الإعدادات ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbydsiNgL7fDAF7-dP9_9lX8QG3_ASsT2qw6Qws1kX4tCA5li3pUFlTFFxYFCk3yqh8q/exec"
dubai_tz = pytz.timezone("Asia/Dubai")

st.title("📍 Attendance System")

# 1. جلب البيانات من شيت الموظفين
try:
    response = requests.get(WEB_APP_URL)
    data = response.json()
    df_emp = pd.DataFrame(data[1:], columns=data[0])
    selected_name = st.selectbox("Select Your Name", [None] + df_emp['Name'].tolist())
except:
    st.error("مش قادر أوصل لشيت الموظفين، تأكد من الرابط!")
    st.stop()

# 2. لو الموظف اختار اسمه
if selected_name:
    st.write(f"Welcome {selected_name}")
    
    # جلب معلومات الموظف الحالي
    emp_info = df_emp[df_emp['Name'] == selected_name].iloc[0]
    
    st.info("جاري تحديد موقعك...")
    loc = streamlit_geolocation()
    
    if loc and loc.get('latitude'):
        # حساب المسافة
        dist = geodesic((loc['latitude'], loc['longitude']), (float(emp_info['Lat']), float(emp_info['Lon']))).meters
        st.write(f"المسافة الحالية: {int(dist)} متر")
        
        # التحقق من النطاق (Radius)
        if dist <= float(emp_info['Radius']):
            st.success("أنت في النطاق الصحيح! يمكنك تسجيل البصمة.")
            img = st.camera_input("التقط صورة البصمة")
            
            if img:
                b64_img = base64.b64encode(img.getvalue()).decode()
                now = datetime.now(dubai_tz).strftime("%Y-%m-%d %H:%M:%S")
                
                col1, col2 = st.columns(2)
                if col1.button("Check-in 📥"):
                    payload = {"name": selected_name, "time": now, "type": "In", "lat": loc['latitude'], "lon": loc['longitude'], "photo": b64_img}
                    requests.post(WEB_APP_URL, json=payload)
                    st.success("تم تسجيل الحضور!")
                
                if col2.button("Check-out 📤"):
                    payload = {"name": selected_name, "time": now, "type": "Out", "lat": loc['latitude'], "lon": loc['longitude'], "photo": b64_img}
                    requests.post(WEB_APP_URL, json=payload)
                    st.success("تم تسجيل الانصراف!")
        else:
            st.error(f"❌ أنت خارج نطاق العمل! المسافة: {int(dist)} متر.")
