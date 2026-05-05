import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import os

# Konfigurasi Halaman & Path
st.set_page_config(page_title="Parking System", layout="centered")
DB_FILE = r'D:\THD\data_parkir.csv'
USER_FILE = r'D:\THD\users.csv'

# --- FUNGSI DATABASE ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            return pd.read_csv(file)
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Inisialisasi Database
if 'users_db' not in st.session_state:
    users = load_data(USER_FILE, ['username', 'password', 'role'])
    if users.empty:
        users = pd.DataFrame([{'username': 'IZ', 'password': '6579', 'role': 'admin'}])
        save_data(users, USER_FILE)
    st.session_state.users_db = users

if 'db' not in st.session_state:
    # Memastikan history lama dari CSV langsung ditarik saat startup
    st.session_state.db = load_data(DB_FILE, ['NOPOL', 'JENIS', 'MASUK', 'KELUAR', 'PETUGAS', 'STATUS'])

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

def login_ui():
    st.title("🔐 Login Parking")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            # Kita paksa kedua sisi (DB dan Input) menjadi String (tulisan) agar sinkron
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

if not st.session_state.logged_in:
    login_ui()
    st.stop()

# --- STYLE & FOOTER ---
def set_bg_and_style():
    # Style dengan warna Biru Tua (Navy) dan Efek Marquee
    footer_style = """
        <style>
        .stTabs, [data-testid="stExpander"], .stAlert, .stDataFrame { 
            background-color: rgba(255, 255, 255, 0.9) !important; 
            border: 2px solid #000080; 
            border-radius: 10px; 
        }
        
        /* Tulisan Biru Tua Solid (Navy) - Tajam & Bold */
        h1, h2, h3, p, label, .stMarkdown { 
            color: #000080 !important; 
            text-shadow: none !important;
            font-weight: bold !important;
        }
        
        /* CSS Khusus Footer dengan Animasi Marquee */
        .footer { 
            position: fixed; 
            left: 0; 
            bottom: 0; 
            width: 100%; 
            background-color: #000080; 
            color: white; 
            padding: 8px 0; 
            z-index: 9999;
            font-family: Arial, sans-serif;
            overflow: hidden; /* Sembunyikan teks yang keluar batas */
        }
        
        .marquee-text {
            display: inline-block;
            white-space: nowrap;
            animation: marquee 15s linear infinite;
            font-size: 16px;
            font-weight: bold;
        }

        @keyframes marquee {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }

        /* Ruang kosong di bawah agar konten utama tidak tertutup footer */
        .main-content { margin-bottom: 60px; }
        </style>
        
        <div class="footer">
            <div class="marquee-text">
                🚨 Selalu Profesional dan Tingkatkan Keamanan — Created by IZ @ 2026 🚨
            </div>
        </div>
    """
    
    # Bagian Background
    path_bg = r'D:\THD\static\background.jpg' 
    if os.path.exists(path_bg):
        with open(path_bg, "rb") as img:
            enc = base64.b64encode(img.read()).decode()
        bg_style = f"""
            <style>
            .stApp {{ 
                background-image: url("data:image/png;base64,{enc}"); 
                background-size: cover; 
                background-attachment: fixed; 
            }}
            </style>
        """
        st.markdown(bg_style, unsafe_allow_html=True) 
    
    st.markdown(footer_style, unsafe_allow_html=True) 

set_bg_and_style()

# --- UI UTAMA & NAVIGASI ---
st.title(f"🚗 🏍️ Apps Parking - Halo, {st.session_state.user}")

# Tambah Menu History agar terlihat jelas
menu = ["📥 MASUK (IN)", "🏠 DI DALAM AREA", "📊 HISTORY DATA"]
if st.session_state.user == "IZ":
    menu.append("👤 CREATE USER")

tab_choice = st.sidebar.radio("Navigasi Menu", menu)

# --- LOGIC SETIAP MENU ---

if tab_choice == "📥 MASUK (IN)":
    st.subheader("Input Kendaraan")
    nopol = st.text_input("NOMOR POLISI", placeholder="Ketik Nopol...").upper()
    jenis = st.selectbox("JENIS:", ["MOBIL PRIBADI", "SEPEDA MOTOR", "MOBIL BARANG"])
    if st.button("PROSES MASUK (IN)"):
        if nopol:
            jam = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = {'NOPOL': nopol, 'JENIS': jenis, 'MASUK': jam, 'KELUAR': '-', 'PETUGAS': st.session_state.user, 'STATUS': 'DI DALAM'}
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(st.session_state.db, DB_FILE) # Simpan otomatis ke CSV
            st.success(f"✅ {nopol} masuk jam {jam}")

elif tab_choice == "🏠 DI DALAM AREA":
    st.subheader("Unit Masih Terparkir")
    df_aktif = st.session_state.db[st.session_state.db['STATUS'] == 'DI DALAM']
    if df_aktif.empty:
        st.info("Area kosong, tidak ada kendaraan di dalam.")
    else:
        for idx, row in df_aktif.iterrows():
            with st.expander(f"📌 {row['NOPOL']} ({row['JENIS']})"):
                st.write(f"Masuk: {row['MASUK']} | Petugas: {row['PETUGAS']}")
                if st.button(f"KLIK OUT - {row['NOPOL']}", key=f"o_{idx}"):
                    jam_out = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.db.at[idx, 'KELUAR'] = jam_out
                    st.session_state.db.at[idx, 'STATUS'] = 'KELUAR'
                    save_data(st.session_state.db, DB_FILE) # Update CSV saat keluar
                    st.rerun()

elif tab_choice == "📊 HISTORY DATA":
    st.subheader("Semua Data Record")
    if st.session_state.db.empty:
        st.info("Belum ada record data.")
    else:
        # Tampilkan history dalam bentuk tabel yang bisa di-scroll
        st.dataframe(st.session_state.db.sort_index(ascending=False), use_container_width=True)
        
        # Tombol Download khusus untuk laporan
        csv = st.session_state.db.to_csv(index=False).encode('utf-8')
        st.download_button("Download Laporan Excel (CSV)", data=csv, file_name=f"Report_Parkir_{datetime.now().strftime('%Y%m%d')}.csv")

elif tab_choice == "👤 CREATE USER":
    st.subheader("Tambah Akun Petugas Baru")
    new_u = st.text_input("Username Baru")
    new_p = st.text_input("Password Baru")
    if st.button("Simpan User Baru"):
        if new_u and new_p:
            new_user = {'username': new_u, 'password': new_p, 'role': 'staff'}
            st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
            save_data(st.session_state.users_db, USER_FILE)
            st.success(f"User {new_u} berhasil dibuat!")

# Sidebar Logout
st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()
