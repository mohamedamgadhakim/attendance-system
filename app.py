import streamlit as st
import pandas as pd
import requests

# رابط الجوجل شيت الخاص بك (تأكد من وضع الرابط الذي يعمل)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbydsiNgL7fDAF7-dP9_9lX8QG3_ASsT2qw6Qws1kX4tCA5li3pUFlTFFxYFCk3yqh8q/exec"

st.set_page_config(page_title="Attendance System", layout="centered")

st.title("📍 Attendance System")

# محاولة جلب بيانات الموظفين
try:
    response = requests.get(WEB_APP_URL)
    if response.status_code == 200:
        data = response.json()
        df_emp = pd.DataFrame(data[1:], columns=data[0])
        
        # اختيار الاسم
        selected_name = st.selectbox("Select Your Name", [None] + df_emp['Name'].tolist())
        
        if selected_name:
            st.write(f"Welcome {selected_name}")
            # هنا سنضع باقي كود البصمة (الذي اتفقنا عليه)
    else:
        st.error("Error: Could not reach the database. Check Web App URL.")
except Exception as e:
    st.error(f"System Error: {e}")
