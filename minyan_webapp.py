import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from google.oauth2.service_account import Credentials
import gspread
from minyan_observer import MinyanObserver

# --- CACHE ---
@st.cache_data(ttl=300)
def load_google_sheet(sheet_url):
    csv_url = sheet_url.replace("/edit?gid=", "/export?format=csv&gid=")
    df = pd.read_csv(csv_url)
    return df

# --- PAGE CONFIG ---
st.set_page_config(page_title="Minyan Observer Dashboard", layout="wide")

# --- STYLES ---
st.markdown("""
<style>
body, .block-container {
    direction: rtl;
    text-align: right;
}
[data-baseweb="slider"] {
    direction: ltr !important;
}
</style>
""", unsafe_allow_html=True)

# --- TITLE ---
st.header("ניתוח נתוני מניין 📊")

# --- DATA SOURCE (no sidebar anymore) ---
st.subheader("מקור הנתונים 📂")

data_source = st.radio(
    "בחר מקור נתונים:",
    ["Google Sheets", "קובץ מקומי"],
    horizontal=True
)

if data_source == "Google Sheets":
    sheet_url = "https://docs.google.com/spreadsheets/d/1lERScRlw-r0LDmyuExE0TrxALEvPIxvQi4ex21mY_D0/export?format=csv&gid=0"
    try:
        data = load_google_sheet(sheet_url)
        st.success("✅ הנתונים נטענו בהצלחה מה-Google Sheets.")
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים: {e}")
        st.stop()
else:
    uploaded_file = st.file_uploader("העלה קובץ CSV", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        st.success("✅ הנתונים נטענו בהצלחה מקובץ מקומי.")
    else:
        st.warning("אנא העלה קובץ נתונים.")
        st.stop()

# --- CREATE OBSERVER ---
gruz = MinyanObserver(data)

# --- EXPANDER FOR DISPLAY OPTIONS ---
with st.expander("⚙️ אפשרויות תצוגה", expanded=True):
    view = st.selectbox(
        "בחר גרף להצגה:",
        [
            "📅 שבוע נוכחי",
            "🕒 מספר שבועות אחרונים",
            "📈 ממוצע לפי שבועות",
            "📊 ממוצע לפי ימים"
        ]
    )

    n_weeks = None
    if view == "🕒 מספר שבועות אחרונים":
        n_weeks = st.slider("כמה שבועות אחרונים להציג?", 1, 10, 2)

# --- SHOW PLOTS ---
if view == "📅 שבוע נוכחי":
    st.subheader("שבוע נוכחי")
    gruz.plot_this_week()
    st.pyplot(plt.gcf())

elif view == "🕒 מספר שבועות אחרונים":
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

# --- FEEDBACK SECTION ---
st.header("משוב ורעיונות לפיתוח 💡")

# Google Sheets setup
FEEDBACK_SHEET_URL = "https://docs.google.com/spreadsheets/d/1GR-fWGhmFvstR6eKHgvCYBt2o_rAbVByKmGxbfUA7Lk/edit?gid=0#gid=0"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)
feedback_sheet = client.open_by_url(FEEDBACK_SHEET_URL).sheet1

feedback = st.text_area("יש לכם רעיון לשיפור הכלי או תכונה חדשה שתרצו לראות?", placeholder="כתבו כאן...")

def save_feedback(message):
    timestamp = datetime.datetime.now().isoformat()
    feedback_sheet.append_row([timestamp, message])

if st.button("שלח"):
    if feedback.strip():
        try:
            save_feedback(feedback)
            st.success("✅ תודה על המשוב! הרעיון שלכם נשמר.")
        except Exception as e:
            st.error(f"❌ שגיאה בשליחת המשוב: {e}")
    else:
        st.warning("אנא כתבו משהו לפני השליחה.")

# --- FOOTER ---
st.markdown("---")
st.caption("🕍 אפליקציית ניתוח נתוני מניין • פותח על ידי עידן")
