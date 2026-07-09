import streamlit as st
import sqlite3
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime
from geopy.distance import geodesic

# إعداد قاعدة البيانات
conn = sqlite3.connect('attendance.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS employees (name TEXT, lat REAL, lon REAL)')
c.execute('CREATE TABLE IF NOT EXISTS logs (name TEXT, time TEXT, type TEXT)')
conn.commit()

st.title("نظام الحضور والانصراف - نظام آلي")

# تاب الإدارة لإدخال البيانات
with st.expander("لوحة التحكم (للإدارة فقط)"):
    admin_pass = st.text_input("كلمة مرور الإدارة", type="password")
    if admin_pass == "1234":
        name_in = st.text_input("اسم الموظف")
        lat_in = st.number_input("Lat", format="%.6f")
        lon_in = st.number_input("Lon", format="%.6f")
        if st.button("إضافة موظف"):
            c.execute("INSERT INTO employees VALUES (?, ?, ?)", (name_in, lat_in, lon_in))
            conn.commit()
            st.success("تم إضافة الموظف")
        
        st.write("سجلات الحضور:")
        df_logs = pd.read_sql("SELECT * FROM logs", conn)
        st.dataframe(df_logs)
        st.download_button("تصدير إكسيل", df_logs.to_csv(), "attendance.csv")

# واجهة الموظف
st.subheader("تسجيل الحضور")
employees = [row[0] for row in c.execute("SELECT name FROM employees").fetchall()]
selected_name = st.selectbox("اختر اسمك", employees)
loc = streamlit_geolocation()

if loc and loc['latitude']:
    img = st.camera_input("التقط صورة للحضور")
    if img and st.button("تأكيد العملية"):
        emp_data = c.execute("SELECT lat, lon FROM employees WHERE name=?", (selected_name,)).fetchone()
        dist = geodesic((loc['latitude'], loc['longitude']), (emp_data[0], emp_data[1])).meters
        
        if dist <= 100: # النطاق 100 متر
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO logs VALUES (?, ?, ?)", (selected_name, now, "حضور/انصراف"))
            conn.commit()
            st.success(f"تم تسجيل {selected_name} بنجاح!")
        else:
            st.error(f"أنت خارج النطاق! المسافة: {int(dist)} متر")
else:
    st.info("يجب تفعيل الموقع في المتصفح")