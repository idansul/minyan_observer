import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import datetime
from minyan_observer import MinyanObserver


@st.cache_data(ttl=300)  # cache for 5 minutes
def load_google_sheet(sheet_url):
    csv_url = sheet_url.replace("/edit?gid=", "/export?format=csv&gid=")
    df = pd.read_csv(csv_url)
    return df


# --- PAGE CONFIG ---
st.set_page_config(page_title="Minyan Observer Dashboard", layout="wide")

st.markdown("""
<style>
/* Everything RTL */
body, .block-container {
    direction: rtl;
    text-align: right;
}

/* Sidebar headings */
[data-testid="stSidebar"] h3 {
    color: #004080;
    text-align: right;
}

/* Sidebar background */
[data-testid="stSidebar"] .css-1d391kg {
    background-color: #f0f8ff;
}

/* Make the slider LTR so number shows properly */
[data-baseweb="slider"] {
    direction: ltr !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* KEEP global RTL for texts (unchanged) */
body, .main, .block-container {
    direction: rtl;
    text-align: right;
}

/* Desktop: do not change sidebar layout at all (safe-guard) */
@media (min-width: 769px) {
    [data-testid="stSidebar"] {
        position: relative !important;
        transform: none !important;
        width: 22rem !important;  /* default Streamlit width */
    }
    [data-testid="stAppViewContainer"] {
        margin-left: 0 !important;
    }
}

/* Mobile-only sidebar behavior */
@media (max-width: 768px) {
    /* make sidebar fixed and initially off-screen */
    [data-testid="stSidebar"] {
        position: fixed !important;
        top: 0;
        right: 0;                 /* RTL: align to right */
        width: 80% !important;
        max-width: 420px;
        height: 100vh !important;
        z-index: 9999 !important;
        transform: translateX(100%); /* push off-screen to the right (RTL) */
        transition: transform 0.28s ease-in-out;
        box-shadow: -4px 0 12px rgba(0,0,0,0.12);
    }

    /* When Streamlit marks the sidebar expanded, bring it in */
    [data-testid="stSidebar"][aria-expanded="true"] {
        transform: translateX(0) !important;
    }

    /* ensure the main app content stays in place under the fixed sidebar */
    [data-testid="stAppViewContainer"] {
        margin-right: 0 !important;
        overflow-x: hidden;
    }

    /* small tweak so the hamburger/toggle doesn't create weird spacing */
    header > div[role="button"] {
        z-index: 10000;
    }
}

/* Make only the slider LTR while leaving everything else RTL */
[data-baseweb="slider"] {
    direction: ltr !important;
}
</style>
""", unsafe_allow_html=True)


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
            data = load_google_sheet(sheet_url)
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



