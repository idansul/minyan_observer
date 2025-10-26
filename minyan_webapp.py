import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import datetime
from minyan_observer import MinyanObserver

# --- PAGE CONFIG ---
st.set_page_config(page_title="Minyan Observer Dashboard", layout="wide")

# --- Connect to the database (creates file if not exists) ---
conn = sqlite3.connect("feedback.db")
cursor = conn.cursor()

# --- Create table once ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    message TEXT
)
""")
conn.commit()

st.markdown("""
<style>
/* Force all text to RTL */
body, .block-container {
    direction: rtl;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)


st.title("ניתוח נתוני מניין 📊")

# --- LOAD DATA ---
st.sidebar.header("מקור הנתונים 📂")
data_source = st.sidebar.radio(
    "בחר מקור נתונים:",
    ["Google Sheets", "קובץ מקומי"]
)

if data_source == "Google Sheets":
    # sheet_url = st.sidebar.text_input("הכנס קישור Google Sheets:")
    sheet_url = "https://docs.google.com/spreadsheets/d/1lERScRlw-r0LDmyuExE0TrxALEvPIxvQi4ex21mY_D0/export?format=csv&gid=0"
    if sheet_url:
        try:
            csv_url = sheet_url.replace("/edit?gid=", "/export?format=csv&gid=")
            data = pd.read_csv(csv_url)
            st.success("✅ הנתונים נטענו בהצלחה מה-Google Sheets.")
        except Exception as e:
            st.error(f"שגיאה בטעינת הנתונים: {e}")
            st.stop()
    else:
        st.warning("אנא הכנס קישור Google Sheets תקין.")
        st.stop()
else:
    uploaded_file = st.sidebar.file_uploader("העלה קובץ CSV", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        st.success("✅ הנתונים נטענו בהצלחה מקובץ מקומי.")
    else:
        st.warning("אנא העלה קובץ נתונים.")
        st.stop()

# --- CREATE OBSERVER ---
gruz = MinyanObserver(data)

# --- SIDEBAR OPTIONS ---
st.sidebar.header("⚙️ אפשרויות תצוגה")
view = st.sidebar.selectbox(
    "בחר גרף להצגה:",
    [
        "📅 שבוע נוכחי",
        "🕒 מספר שבועות אחרונים",
        "📈 ממוצע לפי שבועות",
        "📊 ממוצע לפי ימים"
    ]
)

if view == "📅 שבוע נוכחי":
    st.subheader("שבוע נוכחי")
    gruz.plot_this_week()
    st.pyplot(plt.gcf())

elif view == "🕒 מספר שבועות אחרונים":
    n_weeks = st.sidebar.slider("כמה שבועות אחרונים להציג?", 1, 10, 2)
    st.subheader(f"נתוני {n_weeks} השבועות האחרונים")
    gruz.plot_recent_weeks(n_weeks)
    st.pyplot(plt.gcf())

elif view == "📈 ממוצע לפי שבועות":
    st.subheader("ממוצע וסטיית תקן לפי שבועות")
    gruz.plot_global_stats(var="week")
    st.pyplot(plt.gcf())

elif view == "📊 ממוצע לפי ימים":
    st.subheader("ממוצע וסטיית תקן לפי ימים")
    gruz.plot_global_stats(var="day")
    st.pyplot(plt.gcf())

# --- Streamlit UI ---
st.header("משוב ורעיונות לפיתוח 💡")

feedback = st.text_area("יש לכם רעיון לשיפור הכלי או תכונה חדשה שתרצו לראות?", placeholder="כתבו כאן...")

if st.button("שלח"):
    if feedback.strip():
        cursor.execute("INSERT INTO feedback (timestamp, message) VALUES (?, ?)",
                       (datetime.datetime.now().isoformat(), feedback))
        conn.commit()
        st.success("✅ תודה על המשוב! הרעיון שלכם נשמר.")
    else:
        st.warning("אנא כתבו משהו לפני השליחה.")

# --- FOOTER ---
st.markdown("---")
st.caption("🕍 אפליקציית ניתוח נתוני מניין • פותח על ידי עידן")
