import streamlit as st
import sqlite3
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('attendance.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS logs (name TEXT, time TEXT, action TEXT)')
conn.commit()

st.title("نظام الحضور والانصراف")
name = st.text_input("اسم الموظف")
loc = streamlit_geolocation() # الحصول على الموقع الجغرافي

if st.button("تسجيل حضور/انصراف"):
    if loc:
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO logs VALUES (?, ?, ?)", (name, time, "تسجيل"))
        conn.commit()
        st.success("تم الحضور!")
    else:
        st.error("يرجى السماح للمتصفح بالوصول للموقع")

if st.checkbox("لوحة الإدارة"):
    pwd = st.text_input("كلمة المرور", type="password")
    if pwd == "admin123":
        df = pd.read_sql("SELECT * FROM logs", conn)
        st.dataframe(df)