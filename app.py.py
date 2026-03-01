import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ---------------- DATABASE CONFIG ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute("""CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, roll TEXT UNIQUE, course TEXT, year TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, roll TEXT, date TEXT, status TEXT, UNIQUE(roll, date))""")
    c.execute("""CREATE TABLE IF NOT EXISTS marks 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, roll TEXT, subject TEXT, marks INTEGER)""")
    conn.commit()

init_db()

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="Pro Student Manager", page_icon="🎓", layout="wide")

st.title("🎓 Student Management System")

# Sidebar Navigation
menu = st.sidebar.selectbox("Main Menu", ["Dashboard", "Take Attendance", "Manage Marks", "Bulk Import (CSV)", "Student Registry"])

# Helper: Load Students safely
def get_all_students():
    df = pd.read_sql("SELECT name, roll, course, year FROM students", conn)
    return df.drop_duplicates(subset=['roll'])

# ---------------- 1. DASHBOARD (WITH GRAPHS) ----------------
if menu == "Dashboard":
    st.subheader("📊 Attendance & Enrollment Overview")
    today = str(date.today())
    
    # Fetch Data
    df_students = get_all_students()
    df_attendance = pd.read_sql(f"SELECT * FROM attendance WHERE date = '{today}'", conn)
    
    # Calculations
    total_students = len(df_students)
    present_count = len(df_attendance[df_attendance['status'] == 'Present'])
    absent_count = len(df_attendance[df_attendance['status'] == 'Absent'])
    unmarked_count = total_students - (present_count + absent_count)

    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", total_students)
    m2.metric("Present Today ✅", present_count)
    m3.metric("Absent Today ❌", absent_count)
    m4.metric("Unmarked ⏳", unmarked_count)

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write(f"### Attendance Split for {today}")
        if not df_attendance.empty:
            # Create a chart dataframe
            chart_data = pd.DataFrame({
                'Status': ['Present', 'Absent'],
                'Count': [present_count, absent_count]
            })
            st.bar_chart(data=chart_data, x='Status', y='Count', color="#29b5e8")
        else:
            st.info("No attendance marked for today yet.")

    with col2:
        st.write("### Today's Attendance List")
        if not df_attendance.empty:
            # Merge with student names for a better display
            display_df = pd.merge(df_attendance, df_students, on='roll', how='left')
            st.dataframe(display_df[['roll', 'name', 'status']], use_container_width=True)
        else:
            st.warning("Take attendance to see data here.")

# ---------------- 2. ATTENDANCE ----------------
elif menu == "Take Attendance":
    st.subheader("📅 Daily Attendance Marker")
    today = str(date.today())
    df_students = get_all_students()

    if df_students.empty:
        st.warning("No students in database.")
    else:
        with st.form(key="daily_attendance_form"):
            attendance_updates = []
            cols = st.columns([1, 2, 3])
            cols[0].write("**Roll**")
            cols[1].write("**Name**")
            cols[2].write("**Status**")
            st.divider()

            for index, row in df_students.iterrows():
                r1, r2, r3 = st.columns([1, 2, 3])
                r1.text(row['roll'])
                r2.text(row['name'])
                
                # Dynamic key to prevent duplicates
                user_choice = r3.radio(
                    label=f"Status_{row['roll']}",
                    options=["Present", "Absent"],
                    key=f"att_radio_{index}_{row['roll']}", 
                    horizontal=True,
                    label_visibility="collapsed"
                )
                attendance_updates.append((row['roll'], today, user_choice))

            if st.form_submit_button("Submit Attendance"):
                for record in attendance_updates:
                    c.execute("INSERT OR REPLACE INTO attendance (roll, date, status) VALUES (?,?,?)", record)
                conn.commit()
                st.success("Attendance synced!")
                st.balloons()

# ---------------- 3. MARKS ----------------
elif menu == "Manage Marks":
    st.subheader("📝 Student Marks")
    df_students = get_all_students()
    
    if not df_students.empty:
        with st.form("marks_form"):
            roll = st.selectbox("Select Roll No", df_students['roll'])
            sub = st.text_input("Subject")
            val = st.number_input("Marks", 0, 100)
            if st.form_submit_button("Add Marks"):
                c.execute("INSERT INTO marks (roll, subject, marks) VALUES (?,?,?)", (roll, sub, val))
                conn.commit()
                st.success("Marks added!")

# ---------------- 4. BULK IMPORT ----------------
elif menu == "Bulk Import (CSV)":
    st.subheader("📁 CSV Import")
    uploaded_file = st.file_uploader("Upload CSV (name, roll, course, year)", type="csv")
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        st.dataframe(df_upload)
        if st.button("Confirm Import"):
            try:
                df_upload.to_sql("students", conn, if_exists="append", index=False)
                st.success("Imported successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- 5. REGISTRY ----------------
elif menu == "Student Registry":
    st.subheader("⚙️ Student Management")
    with st.form("reg_form"):
        n = st.text_input("Name")
        r = st.text_input("Roll")
        c_name = st.text_input("Course")
        y = st.selectbox("Year", ["1st", "2nd", "3rd", "4th"])
        if st.form_submit_button("Register"):
            try:
                c.execute("INSERT INTO students (name, roll, course, year) VALUES (?,?,?,?)", (n, r, c_name, y))
                conn.commit()
                st.success("Student added!")
            except:
                st.error("Roll number already exists.")