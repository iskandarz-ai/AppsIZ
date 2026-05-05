import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
import os

# --- KONFIGURASI CLOUD ---
st.set_page_config(page_title="IZ Parking Cloud", layout="centered")

# Koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Ganti fungsi load_data_sheets Bos di GitHub menjadi ini:
def load_data_sheets(tab_name):
    # Kita tambahkan parameter spreadsheet secara eksplisit dari Secrets
    # supaya Streamlit tidak bingung mencari file-nya
    return conn.read(
        spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"],
        worksheet=tab_name,
        ttl=0
    )

def save_to_sheets(df, tab_name):
    # Langsung update ke koneksi tanpa sebut URL lagi
    conn.update(worksheet=tab_name, data=df)
    st.cache_data.clear()
# --- INISIALISASI DATABASE ---
if 'users_db' not in st.session_state:
    try:
        st.session_state.users_db = load_data_sheets("users")
    except:
        st.error("Gagal ambil data Users. Cek izin Share di Google Sheets, Bos!")
        st.stop()

if 'db' not in st.session_state:
    try:
        st.session_state.db = load_data_sheets("data_parkir")
    except:
        st.session_state.db = pd.DataFrame(columns=['NOPOL', 'JENIS', 'MASUK', 'KELUAR', 'PETUGAS', 'STATUS'])

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if not st.session_state.logged_in:
    st.title("🔐 Login Parking")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user_match = st.session_state.users_db[
                (st.session_state.users_db['username'].astype(str) == str(u)) & 
                (st.session_state.users_db['password'].astype(str) == str(p))
            ]
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Username atau Password salah, Bos!")
    st.stop()

# --- STYLE & DESIGN ---
def set_design():
    path_bg = "static/background.jpg" 
    if os.path.exists(path_bg):
        with open(path_bg, "rb") as img:
            enc = base64.b64encode(img.read()).decode()
        st.markdown(f"""<style>.stApp {{ background-image: url("data:image/png;base64,{enc}"); background-size: cover; background-attachment: fixed; }}</style>""", unsafe_allow_html=True)
    
    st.markdown("""
        <style>
        .stTabs, [data-testid="stExpander"], .stAlert, .stDataFrame { background-color: rgba(255, 255, 255, 0.9) !important; border: 2px solid #000080; border-radius: 10px; }
        h1, h2, h3, p, label, .stMarkdown { color: #000080 !important; font-weight: bold !important; text-shadow: none !important; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #000080; color: white; padding: 8px 0; z-index: 9999; overflow: hidden; }
        .marquee-text { display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; font-size: 16px; font-weight: bold; }
        @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
        </style>
        <div class="footer"><div class="marquee-text">🚨 Selalu Profesional dan Tingkatkan Keamanan — Created by IZ @ 2026 🚨</div></div>
    """, unsafe_allow_html=True)

set_design()

# --- NAVIGASI & MENU ---
st.title(f"🚗 🏍️ Apps Parking - Halo, {st.session_state.user}")
menu = ["📥 MASUK (IN)", "🏠 DI DALAM AREA", "📊 HISTORY DATA"]
if st.session_state.user == "IZ": menu.append("👤 CREATE USER")
tab_choice = st.sidebar.radio("Navigasi Menu", menu)

if tab_choice == "📥 MASUK (IN)":
    st.subheader("Input Kendaraan")
    nopol = st.text_input("NOMOR POLISI").upper()
    jenis = st.selectbox("JENIS:", ["MOBIL PRIBADI", "SEPEDA MOTOR", "MOBIL BARANG"])
    if st.button("PROSES MASUK (IN)"):
        if nopol:
            jam = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = pd.DataFrame([{'NOPOL': nopol, 'JENIS': jenis, 'MASUK': jam, 'KELUAR': '-', 'PETUGAS': st.session_state.user, 'STATUS': 'DI DALAM'}])
            st.session_state.db = pd.concat([st.session_state.db, new_entry], ignore_index=True)
            save_to_sheets(st.session_state.db, "data_parkir")
            st.success(f"✅ {nopol} Masuk jam {jam}")

elif tab_choice == "🏠 DI DALAM AREA":
    st.subheader("Unit Masih Terparkir")
    df_aktif = st.session_state.db[st.session_state.db['STATUS'] == 'DI DALAM']
    if df_aktif.empty:
        st.info("Area kosong.")
    else:
        for idx, row in df_aktif.iterrows():
            with st.expander(f"📌 {row['NOPOL']} ({row['JENIS']})"):
                if st.button(f"KLIK OUT - {row['NOPOL']}", key=f"out_{idx}"):
                    st.session_state.db.at[idx, 'KELUAR'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.db.at[idx, 'STATUS'] = 'KELUAR'
                    save_to_sheets(st.session_state.db, "data_parkir")
                    st.rerun()

elif tab_choice == "📊 HISTORY DATA":
    st.subheader("Semua Data Record")
    st.dataframe(st.session_state.db.sort_index(ascending=False), use_container_width=True)
    csv = st.session_state.db.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.csv")

elif tab_choice == "👤 CREATE USER":
    st.subheader("Tambah Petugas")
    new_u = st.text_input("Username")
    new_p = st.text_input("Password")
    if st.button("Simpan User"):
        if new_u and new_p:
            new_user = pd.DataFrame([{'username': new_u, 'password': new_p, 'role': 'staff'}])
            st.session_state.users_db = pd.concat([st.session_state.users_db, new_user], ignore_index=True)
            save_to_sheets(st.session_state.users_db, "users")
            st.success(f"User {new_u} dibuat!")

st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
