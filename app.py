# ============================================
# KARBONAT P2 - GSTC / TGA Uyumlu Karbon Ayak İzi
# Akıllı Sürdürülebilirlik Raporlaması
# v0.4 - Yeniden Tasarım
# ============================================

import pandas as pd
from datetime import datetime
from io import BytesIO

import streamlit as st

from factors import EMISSION_FACTORS, KATEGORI_ACIKLAMALARI
from emission_calc import (
    hesapla_scope_ayrimi,
    hesapla_normalize_metrikler,
    en_agir_kaynaklar,
)
from tga_tables import (
    format_donem,
    tum_tablolar,
)
from green_report import save_green_report
from icerik_hub import (
    ICERIK_TURLERI,
    ISKELETLER,
    TEMALAR,
    tercih_sorulari,
    varsayilan_tercih,
)
from data_store import (
    list_facilities,
    get_facility,
    save_facility,
    list_records,
    get_record,
    get_previous_record,
    save_record,
    create_user,
    verify_login,
    get_user_by_id,
    count_facilities,
    get_content_prefs,
    save_content_prefs,
)

# ==============================================
# MARKA KİMLİĞİ - KARBON & ORMAN
# ==============================================
INK      = "#17211b"   # grafit (karbon)
PRIMARY  = "#1d6b45"   # zümrüt
PRIMARY2 = "#2e8b57"   # orman
ACCENT   = "#3da873"   # yaprak
SAGE     = "#b7d8c2"   # açık adaçayı
MIST     = "#eef4ee"   # sisli yeşil
CARD     = "#ffffff"
PAPER    = "#f6f8f4"
BORDER   = "#e3e9e3"
MUTED    = "#6b7a70"
AMBER    = "#d99a3d"   # öne çıkan
TERRA    = "#c0573d"

st.set_page_config(
    page_title="KarbonAT P2 - Otel Karbon Ayak İzi",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================
# STİL (SIFIRDAN)
# ==============================================
st.markdown(f"""
<style>
    :root {{
        --ink: {INK}; --primary: {PRIMARY}; --accent: {ACCENT};
        --sage: {SAGE}; --mist: {MIST}; --card: {CARD};
        --paper: {PAPER}; --border: {BORDER}; --muted: {MUTED};
        --amber: {AMBER}; --terra: {TERRA};
    }}

    /* ===== GENEL ===== */
    .stApp {{ background: var(--paper); }}
    html, body, p, li, span, div, label {{ color: var(--ink); font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; }}
    h1, h2, h3, h4, h5, h6 {{ color: var(--ink); font-weight: 750; letter-spacing: -0.3px; }}
    h1 {{ font-size: 32px; margin-top: 0.2rem; }}
    h3 {{ font-size: 20px; }}
    [data-testid="stSidebar"] {{ background: #fff; border-right: 1px solid var(--border); }}
    [data-testid="stSidebarNav"] {{ display: none; }}
    .block-container {{ padding-top: 1.6rem; max-width: 1180px; }}

    /* ===== SIDEBAR ===== */
    .sb-brand {{ font-size: 21px; font-weight: 800; color: var(--primary); margin-bottom: 2px; }}
    .sb-tag {{ font-size: 11px; color: var(--muted); margin-bottom: 14px; }}
    .sb-card {{
        background: var(--mist); border: 1px solid var(--border);
        border-radius: 14px; padding: 14px 16px; margin: 10px 0;
    }}
    .sb-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); margin-bottom: 6px; }}
    .sb-value {{ font-weight: 700; font-size: 15px; color: var(--ink); }}
    .sb-step {{ display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 10px; margin: 4px 0; font-size: 14px; }}
    .sb-step.active {{ background: var(--mist); color: var(--primary); font-weight: 700; }}
    .sb-step.done {{ color: var(--muted); }}
    .sb-num {{
        width: 22px; height: 22px; border-radius: 50%; display: flex;
        align-items: center; justify-content: center; font-size: 12px; font-weight: 700;
        background: var(--border); color: var(--muted); flex-shrink: 0;
    }}
    .sb-step.active .sb-num {{ background: var(--primary); color: #fff; }}
    .sb-step.done .sb-num {{ background: var(--sage); color: var(--primary); }}

    /* ===== BUTONLAR ===== */
    .stButton > button {{
        background: var(--primary); color: #fff; border: none;
        padding: 12px 28px; border-radius: 12px; font-weight: 700; font-size: 15px;
        transition: all 0.18s ease; box-shadow: 0 3px 10px rgba(29,107,69,0.18);
    }}
    .stButton > button:hover {{ background: var(--primary2); transform: translateY(-1px); }}
    button[kind="secondary"] {{
        background: #fff !important; color: var(--primary) !important;
        border: 1.5px solid var(--primary) !important; box-shadow: none !important;
    }}
    .stDownloadButton > button {{
        background: var(--primary); color: #fff; border: none;
        padding: 12px 24px; border-radius: 12px; font-weight: 700; font-size: 15px;
        transition: all 0.18s ease;
    }}
    .stDownloadButton > button:hover {{ background: var(--primary2); }}

    /* ===== KARTLAR ===== */
    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 14px 0; }}
    .kpi-card {{
        background: var(--card); border: 1px solid var(--border); border-radius: 16px;
        padding: 18px 20px; box-shadow: 0 1px 3px rgba(23,33,27,0.05);
    }}
    .kpi-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); margin-bottom: 6px; }}
    .kpi-value {{ font-size: 26px; font-weight: 800; color: var(--ink); }}
    .kpi-sub {{ font-size: 12.5px; color: var(--muted); margin-top: 4px; }}

    .data-card {{
        background: var(--card); border: 1px solid var(--border); border-radius: 16px;
        padding: 20px 22px; margin: 12px 0; box-shadow: 0 1px 3px rgba(23,33,27,0.04);
    }}

    .banner {{
        background: var(--mist); border: 1px solid var(--border); border-left: 4px solid var(--accent);
        border-radius: 12px; padding: 13px 18px; margin: 10px 0; color: var(--ink); font-size: 14px;
    }}

    .chip {{
        background: var(--mist); color: var(--primary); border: 1px solid var(--sage);
        padding: 5px 14px; border-radius: 20px; font-weight: 700; font-size: 13px;
        display: inline-block; margin: 2px 6px 2px 0;
    }}

    .hero {{ text-align: center; padding: 46px 20px 30px; }}
    .hero .logo {{ font-size: 58px; }}
    .hero h1 {{ font-size: 42px; margin: 6px 0; }}
    .hero p {{ color: var(--muted); font-size: 16px; max-width: 600px; margin: 0 auto; }}

    .section-title {{ font-size: 17px; font-weight: 750; color: var(--ink); margin: 22px 0 10px; }}

    .footer {{ text-align: center; color: var(--muted); font-size: 12.5px; padding: 34px 0 14px; }}

    /* ===== FORM ===== */
    .stTextInput input, .stNumberInput input, .stDateInput input {{
        border-radius: 10px; border: 1px solid var(--border);
    }}
    .stExpander {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; margin-bottom: 8px; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent; border-radius: 10px 10px 0 0; padding: 10px 18px;
        font-weight: 600; color: var(--muted); border-bottom: 2.5px solid transparent;
    }}
    .stTabs [aria-selected="true"] {{
        color: var(--primary); border-bottom-color: var(--primary);
    }}
    [data-testid="stMetricValue"] {{ font-size: 24px; font-weight: 800; color: var(--primary); }}
    [data-testid="stMetricLabel"] {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.6px; }}
</style>
""", unsafe_allow_html=True)


# ==============================================
# OTURUM
# ==============================================
def init_session():
    defaults = {
        "user": None,
        "step": 0,
        "facility_id": None,
        "tesis": {},
        "period": datetime.today().strftime("%Y-%m"),
        "musteri": 0,
        "dolu_oda_gun": 0,
        "tuketim": {},
        "sonuc": None,
        "history": [],
        "kategori_totallari": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()

KATEGORI_BIRIM = {
    "Elektrik": "kWh",
    "Doğal Gaz": "m³ / kg",
    "Su": "m³",
    "Gıda Tüketimi": "kg",
    "Atık Yönetimi": "kg",
    "Kimyasal Tüketimi": "L",
}

STEP_ISIMLERI = [
    ("🏠", "Tesis"),
    ("🏨", "Profil"),
    ("📊", "Veri Girişi"),
    ("🧮", "Hesaplama"),
    ("📄", "Rapor"),
    ("🌿", "İçerikler"),
]


# ==============================================
# SIDEBAR
# ==============================================
def sidebar():
    with st.sidebar:
        st.markdown('<div class="sb-brand">🌿 KarbonAT <span style="color:#d99a3d;">P2</span></div>'
                    '<div class="sb-tag">GSTC / TGA Uyumlu Raporlama</div>', unsafe_allow_html=True)

        # Tesis bilgisi
        t = st.session_state.tesis
        if t and t.get("ad"):
            st.markdown(
                f'<div class="sb-card">'
                f'<div class="sb-label">Tesis</div>'
                f'<div class="sb-value">{t["ad"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="sb-card"><div class="sb-label">Tesis</div>'
                f'<div class="sb-value" style="color:#b6beb8;">Seçilmedi</div></div>',
                unsafe_allow_html=True,
            )

        if st.session_state.step >= 2 and st.session_state.tesis:
            st.markdown(
                f'<div class="sb-card"><div class="sb-label">Dönem</div>'
                f'<div class="sb-value">📅 {format_donem(st.session_state.period)}</div></div>',
                unsafe_allow_html=True,
            )

        # Adım göstergesi
        st.markdown(f'<div class="sb-label" style="margin-top:14px;">İlerleme</div>', unsafe_allow_html=True)
        step = st.session_state.step
        for i, (emoji, isim) in enumerate(STEP_ISIMLERI):
            cls = "active" if i == step else ("done" if i < step else "")
            st.markdown(
                f'<div class="sb-step {cls}"><div class="sb-num">{i + 1}</div>'
                f'<span>{emoji} {isim}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if st.button("🔄 Sıfırla", use_container_width=True, type="secondary"):
            for k in ["step", "facility_id", "tesis", "tuketim", "sonuc", "history", "kategori_totallari"]:
                if k in st.session_state:
                    del st.session_state[k]
            init_session()
            st.rerun()

        st.markdown('<div class="sb-label" style="margin-top:20px;">Oturum</div>', unsafe_allow_html=True)
        if st.session_state.user:
            u = st.session_state.user
            st.markdown(
                f'<div class="sb-card">'
                f'<div class="sb-label">👤 Kullanıcı</div>'
                f'<div class="sb-value">{u.get("fullname", u["username"])}</div>'
                f'<div style="font-size:12px; color:#6b7a70;">@{u["username"]} · {count_facilities(u["id"])} otel</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("🚪 Çıkış Yap", use_container_width=True, type="secondary"):
                for k in ["user", "step", "facility_id", "tesis", "tuketim", "sonuc", "history"]:
                    if k in st.session_state:
                        del st.session_state[k]
                init_session()
                st.rerun()


# ==============================================
# YARDIMCILAR
# ==============================================
def _period_options():
    options = []
    now = datetime.today()
    y, m = now.year, now.month
    for _ in range(24):
        options.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return options


def _sifir_tuketim():
    tuk = {}
    for kategori in EMISSION_FACTORS:
        tuk[kategori] = {}
        for alt_tur in EMISSION_FACTORS[kategori]:
            tuk[kategori][alt_tur] = 0.0
    return tuk


def _kategori_df(kategori, tuketim):
    rows = []
    for alt_tur, faktor in EMISSION_FACTORS.get(kategori, {}).items():
        miktar = tuketim.get(kategori, {}).get(alt_tur, 0.0)
        rows.append({"Alt Tür": alt_tur, "Miktar": round(miktar, 2),
                     "Emisyon Faktörü": faktor, "Emisyon (kg)": round(miktar * faktor, 2)})
    return pd.DataFrame(rows)


def _tesis_ozet(t):
    return f'{t["m2"]} m² · {t["oda"]} oda · {t["personel"]} personel'


def _hesapla(tesis, tuketim, musteri, dolu_oda_gun):
    scope_data = hesapla_scope_ayrimi(tuketim)
    metrikler = hesapla_normalize_metrikler(
        scope_data["toplam"], tesis["m2"], tesis["oda"], tesis["personel"],
        musteri, dolu_oda_gun,
    )
    metrikler["scope1_kg"] = round(scope_data["scope1"], 2)
    metrikler["scope2_kg"] = round(scope_data["scope2"], 2)
    metrikler["scope3_kg"] = round(scope_data["scope3"], 2)
    en_agir = en_agir_kaynaklar(scope_data["kategori_toplamlari"])
    return {
        "tesis": {**tesis, "musteri": musteri, "dolu_oda_gun": dolu_oda_gun},
        "statik": {"atik_bertaraf": tesis["atik_bertaraf"], "yenilenebilir": tesis["yenilenebilir"]},
        "tuketim": tuketim,
        "scope": scope_data,
        "metrikler": metrikler,
        "en_agir": en_agir,
    }


def _color_for_pct(pct):
    if pct > 40:
        return TERRA
    elif pct > 20:
        return PRIMARY
    elif pct > 10:
        return PRIMARY2
    else:
        return SAGE


# ==============================================
# GİRİŞ / KAYIT
# ==============================================
def auth_screen():
    st.markdown("""
    <div class="hero">
        <div class="logo">🌿</div>
        <h1>KarbonAT P2</h1>
        <p>GSTC / TGA uyumlu karbon ayak izi ve sürdürülebilirlik raporlaması</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([2, 3, 2])[1]

    with col:
        secim = st.segmented_control(
            "Giriş türü",
            options=["🔑 Giriş Yap", "✨ Kayıt Ol"],
            default="🔑 Giriş Yap",
            key="auth_mode",
            label_visibility="collapsed",
        )

        if secim == "🔑 Giriş Yap":
            username = st.text_input("Kullanıcı adı", key="auth_uname")
            password = st.text_input("Şifre", type="password", key="auth_pw")
            if st.button("Giriş Yap", use_container_width=True):
                user = verify_login(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.step = 0
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı.")
        else:
            yeni_adi = st.text_input("Ad Soyad", key="reg_name")
            yeni_uname = st.text_input("Kullanıcı adı", key="reg_uname")
            yeni_pw = st.text_input("Şifre (en az 4 karakter)", type="password", key="reg_pw")
            if st.button("Hesap Oluştur", use_container_width=True):
                if len(yeni_pw) < 4:
                    st.error("Şifre en az 4 karakter olmalı.")
                else:
                    user = create_user(yeni_uname, yeni_pw, yeni_adi)
                    if user:
                        st.session_state.user = user
                        st.session_state.step = 0
                        st.rerun()
                    else:
                        st.error("Bu kullanıcı adı zaten alınmış.")


# ==============================================
# ADIM 0 - TESİS SEÇİMİ (PROFİLİM / OTELLERİM)
# ==============================================
def adim_tesis_secimi():
    st.markdown("""
    <div class="hero">
        <div class="logo">🌿</div>
        <h1>KarbonAT P2</h1>
        <p>Aylık tüketim verilerinizi TGA takip tablolarına ve karbon ayak izi raporuna dönüştürür.</p>
    </div>
    """, unsafe_allow_html=True)

    user = st.session_state.user
    facilities = list_facilities(user["id"])
    col = st.columns([2, 3, 2])[1]

    if facilities:
        with col:
            st.markdown(
                f'<div class="section-title">🏨 Profilim · Otellerim '
                f'<span style="color:#6b7a70; font-weight:500;">({len(facilities)})</span></div>',
                unsafe_allow_html=True,
            )
            secenekler = {t["ad"]: t["id"] for t in facilities}
            secim = st.selectbox("Tesisinizi seçin", list(secenekler.keys()))
            st.session_state.facility_id = secenekler[secim]
            st.session_state.tesis = get_facility(st.session_state.facility_id)

            kayitlar = list_records(st.session_state.facility_id)
            if kayitlar:
                son = kayitlar[-1]
                st.markdown(
                    f'<div class="banner">📅 Son kayıt: <strong>{format_donem(son["period"])}</strong> · '
                    f'{son["sonuc"]["metrikler"]["toplam_ton"]} ton CO₂e</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("📊 Veri Girişi", use_container_width=True):
                    st.session_state.history = list_records(st.session_state.facility_id)
                    st.session_state.step = 2
                    st.rerun()
            with c2:
                if st.button("✏️ Profili Düzenle", use_container_width=True, type="secondary"):
                    st.session_state.step = 1
                    st.rerun()
            with c3:
                if st.button("🌿 İçerik Merkezi", use_container_width=True, type="secondary"):
                    st.session_state.step = 5
                    st.rerun()
            if st.button("＋ Yeni Tesis Oluştur", use_container_width=True, type="secondary"):
                st.session_state.tesis = {}
                st.session_state.facility_id = None
                st.session_state.step = 1
                st.rerun()
    else:
        with col:
            st.markdown('<div class="section-title">Henüz oteliniz yok</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="banner">👋 Hoş geldiniz, <strong>{user.get("fullname", user["username"])}</strong>! '
                f'İlk tesis profilinizi oluşturarak başlayın.</div>',
                unsafe_allow_html=True,
            )
            if st.button("▶ Tesis Oluştur", use_container_width=True):
                st.session_state.step = 1
                st.rerun()


# ==============================================
# ADIM 1 - TESİS PROFİLİ
# ==============================================
def adim_tesis():
    st.markdown('<h1>🏨 Tesis Profili</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7a70;">Bir kerelik bilgiler. Sonradan değiştirilebilir.</p>', unsafe_allow_html=True)

    t = st.session_state.tesis or {}
    st.markdown('<div class="section-title">Kimlik & Kapasite</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        tesis_adi = st.text_input("Tesis / Otel adı", value=t.get("ad", ""), placeholder="Örn. Grand Horizon")
    with col2:
        m2 = st.number_input("Toplam kapalı alan (m²)", min_value=1, value=int(t.get("m2", 1000)), step=100)
    with col3:
        oda = st.number_input("Toplam oda sayısı", min_value=1, value=int(t.get("oda", 50)), step=10)

    col4, col5 = st.columns(2)
    with col4:
        personel = st.number_input("Personel sayısı", min_value=1, value=int(t.get("personel", 20)), step=5)
    with col5:
        st.caption("Müşteri ve oda-gün sayıları aylık veri girişinde girilir.")

    st.markdown('<div class="section-title">Sürdürülebilirlik Bağlamı</div>', unsafe_allow_html=True)
    col6, col7 = st.columns(2)
    with col6:
        atik_secenek = ["Geri dönüşüm + çöp (karışık)", "Ağırlıklı geri dönüşüm", "Çoğunlukla çöp + kompost"]
        atik_idx = t.get("atik_bertaraf_idx", 0)
        if not isinstance(atik_idx, int) or not 0 <= atik_idx < len(atik_secenek):
            atik_idx = 0
        atik_bertaraf = st.selectbox("Ağırlıklı atık bertaraf yöntemi", atik_secenek, index=atik_idx)
    with col7:
        yenilenebilir = st.slider(
            "Yenilenebilir elektrik oranı (%)", 0, 100,
            value=int(t.get("yenilenebilir", 30)), step=5,
            help="Şebeke elektriğinin YEK-G sertifikalı (yenilenebilir) kısmı",
        )

    st.markdown("---")
    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Geri", use_container_width=True):
            st.session_state.step = 0
            st.rerun()
    with col_next:
        disabled = not (tesis_adi and m2 and oda and personel)
        if st.button("💾 Kaydet ve Devam", use_container_width=True, disabled=disabled):
            tesis = {
                "ad": tesis_adi,
                "m2": int(m2),
                "oda": int(oda),
                "personel": int(personel),
                "atik_bertaraf": atik_bertaraf,
                "atik_bertaraf_idx": atik_secenek.index(atik_bertaraf),
                "yenilenebilir": yenilenebilir,
            }
            if st.session_state.facility_id:
                tesis["id"] = st.session_state.facility_id
            tesis = save_facility(tesis, owner_id=st.session_state.user["id"])
            st.session_state.tesis = tesis
            st.session_state.facility_id = tesis["id"]
            st.session_state.history = list_records(tesis["id"])
            st.session_state.step = 2
            st.rerun()


# ==============================================
# ADIM 2 - AYLIK VERİ (TABLO BAZLI GİRİŞ)
# ==============================================
def adim_veri():
    tesis = st.session_state.tesis
    st.markdown(f'<h1>📊 Aylık Veri Girişi</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="chip">🌿 {tesis["ad"]}</div>'
        f'<div class="chip">📐 {_tesis_ozet(tesis)}</div>',
        unsafe_allow_html=True,
    )

    # Dönem seçimi
    options = _period_options()
    current = st.session_state.period
    if current not in options:
        options.insert(0, current)
    idx = options.index(current) if current in options else 0
    secilen = st.selectbox(
        "📅 Veri dönemi",
        options,
        index=idx,
        format_func=format_donem,
    )
    st.session_state.period = secilen

    # Kayıt / önceki dönem yükle
    mevcut = get_record(st.session_state.facility_id, secilen)
    onceki = get_previous_record(st.session_state.facility_id, secilen)

    if mevcut:
        st.markdown(
            f'<div class="banner">✅ {format_donem(secilen)} için kayıt var. '
            f'Değerleri düzenleyip yeniden hesaplayabilirsiniz.</div>',
            unsafe_allow_html=True,
        )
    elif onceki:
        st.markdown(
            f'<div class="banner">📎 Önceki dönem ({format_donem(onceki["period"])}) '
            f'değerleri alt türlere yüklendi. Düzenleyebilirsiniz.</div>',
            unsafe_allow_html=True,
        )

    # Tuketim verisini yükle: kayıt varsa ondan, önceki dönemden, yoksa sıfır
    if "_load_period" not in st.session_state or st.session_state._load_period != secilen:
        base = None
        if mevcut:
            base = mevcut["tuketim"]
        elif onceki:
            base = onceki["tuketim"]
        tuk = {}
        for kat in EMISSION_FACTORS:
            tuk[kat] = {}
            for alt in EMISSION_FACTORS[kat]:
                tuk[kat][alt] = base.get(kat, {}).get(alt, 0.0) if base else 0.0
        st.session_state.tuketim = tuk
        st.session_state.musteri = mevcut["musteri"] if mevcut else (onceki["musteri"] if onceki else 0)
        st.session_state.dolu_oda_gun = mevcut["dolu_oda_gun"] if mevcut else (onceki["dolu_oda_gun"] if onceki else 0)
        st.session_state._load_period = secilen

    tuketim = st.session_state.tuketim

    # Operasyon
    st.markdown('<div class="section-title">🛏️ Bu Ayki Operasyon</div>', unsafe_allow_html=True)
    col_m, col_d = st.columns(2)
    with col_m:
        musteri = st.number_input("Müşteri sayısı (konaklayan kişi)", min_value=0, step=10,
                                  value=int(st.session_state.musteri),
                                  help="Örn: 1 aile = 4 kişi")
    with col_d:
        dolu_oda_gun = st.number_input("Satılan oda-gün sayısı", min_value=0, step=50,
                                       value=int(st.session_state.dolu_oda_gun),
                                       help="Toplam oda × doluluk × gün (HCMI)")
    st.session_state.musteri = musteri
    st.session_state.dolu_oda_gun = dolu_oda_gun

    # TGA tablolarına göre sekmeler
    st.markdown('<div class="section-title">🗂️ TGA Takip Tabloları</div>', unsafe_allow_html=True)

    sekmeler = [
        ("🔌 Elektrik · Tablo 10", "Elektrik"),
        ("🔥 Doğal Gaz", "Doğal Gaz"),
        ("🚿 Su · Tablo 12", "Su"),
        ("🍽️ Gıda", "Gıda Tüketimi"),
        ("♻️ Atık · Tablo 13", "Atık Yönetimi"),
        ("🧪 Kimyasal", "Kimyasal Tüketimi"),
    ]

    tabs = st.tabs([s[0] for s in sekmeler])
    for tab, (_, kat) in zip(tabs, sekmeler):
        with tab:
            aciklama = KATEGORI_ACIKLAMALARI.get(kat, "")
            if aciklama:
                st.caption(aciklama)

            df = _kategori_df(kat, tuketim)
            edited = st.data_editor(
                df,
                key=f"ed_{secilen}_{kat}",
                hide_index=True,
                num_rows="fixed",
                disabled=["Alt Tür", "Emisyon Faktörü", "Emisyon (kg)"],
                column_config={
                    "Alt Tür": st.column_config.TextColumn("Alt Tür", width="large"),
                    "Miktar": st.column_config.NumberColumn(
                        f"Miktar ({KATEGORI_BIRIM.get(kat, '')})",
                        min_value=0.0, step=1.0, format="%.2f"),
                    "Emisyon Faktörü": st.column_config.NumberColumn("EF", format="%.3f"),
                    "Emisyon (kg)": st.column_config.NumberColumn("Emisyon (kg)", format="%.2f"),
                },
                use_container_width=True,
            )

            # edited -> tuketim'e yaz
            tuketim[kat] = {}
            for _, row in edited.iterrows():
                tuketim[kat][row["Alt Tür"]] = float(row["Miktar"])

            kat_toplam = sum(
                miktar * EMISSION_FACTORS[kat].get(alt, 0.0)
                for alt, miktar in tuketim[kat].items()
            )
            aktif = sum(1 for v in tuketim[kat].values() if v > 0)
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Kategori Emisyonu", f"{kat_toplam:,.1f} kg CO₂e")
            with c2:
                st.caption(f"{aktif} alt tür dolu · Emisyon otomatik hesaplanır")

    st.session_state.tuketim = tuketim

    # Canlı özet
    st.markdown('<div class="section-title">🧮 Canlı Özet</div>', unsafe_allow_html=True)
    onizleme = _hesapla(tesis, tuketim, musteri, dolu_oda_gun)
    m = onizleme["metrikler"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam", f"{m['toplam_ton']} ton CO₂e")
    c2.metric("Oda-Gün", f"{m['oda_gun_kg']} kg")
    c3.metric("Müşteri Başına", f"{m['musteri_kg']} kg")
    c4.metric("m² Başına", f"{m['m2_aylik_kg']} kg")

    st.markdown("---")
    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Geri", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("🧮 Hesapla ve Raporla", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


# ==============================================
# ADIM 3 - HESAPLAMA
# ==============================================
def adim_hesap():
    st.markdown('<h1>🧮 Hesaplama</h1>', unsafe_allow_html=True)
    tesis = st.session_state.tesis
    period = st.session_state.period
    tuketim = st.session_state.tuketim

    with st.spinner("Hesaplanıyor..."):
        sonuc = _hesapla(
            tesis, tuketim,
            st.session_state.musteri,
            st.session_state.dolu_oda_gun,
        )
        save_record({
            "fac_id": st.session_state.facility_id,
            "period": period,
            "musteri": st.session_state.musteri,
            "dolu_oda_gun": st.session_state.dolu_oda_gun,
            "tuketim": tuketim,
            "sonuc": sonuc,
        })
        st.session_state.history = list_records(st.session_state.facility_id)

    st.session_state.sonuc = sonuc
    st.session_state.step = 4
    st.rerun()


# ==============================================
# ADIM 4 - SONUÇ + RAPOR (TEKİLLEŞTİRİLMİŞ)
# ==============================================
def adim_sonuc():
    st.markdown('<h1>📄 Karbon Ayak İzi Sonucu</h1>', unsafe_allow_html=True)

    if st.session_state.sonuc is None:
        st.warning("Önce hesaplama yapın.")
        return

    r = st.session_state.sonuc
    tesis = r["tesis"]
    scope = r["scope"]
    metrik = r["metrikler"]
    en_agir = r["en_agir"]
    period = st.session_state.period
    tuketim = r["tuketim"]

    st.markdown(
        f'<div class="chip">🌿 {tesis["ad"]}</div>'
        f'<div class="chip">📅 {format_donem(period)}</div>',
        unsafe_allow_html=True,
    )

    # KPI
    st.markdown('<div class="section-title">🔢 Temel Göstergeler</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-label">🌍 Toplam Emisyon</div>
        <div class="kpi-value">{metrik['toplam_ton']} ton CO₂e</div>
        <div class="kpi-sub">{metrik['toplam_kg']:,.0f} kg · aylık</div></div>
      <div class="kpi-card"><div class="kpi-label">🛏️ Oda-Gün Başına</div>
        <div class="kpi-value">{metrik['oda_gun_kg']} kg</div>
        <div class="kpi-sub">HCMI standart metrik</div></div>
      <div class="kpi-card"><div class="kpi-label">📐 m² Başına</div>
        <div class="kpi-value">{metrik['m2_aylik_kg']} kg</div>
        <div class="kpi-sub">Aylık, m² başına</div></div>
      <div class="kpi-card"><div class="kpi-label">👤 Müşteri Başına</div>
        <div class="kpi-value">{metrik['musteri_kg']} kg</div>
        <div class="kpi-sub">Konaklayan kişi başına</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Geçmiş karşılaştırma
    onceki = get_previous_record(st.session_state.facility_id, period)
    if onceki:
        om = onceki["sonuc"]["metrikler"]
        if om.get("toplam_kg", 0) > 0:
            delta = (metrik["toplam_kg"] - om["toplam_kg"]) / om["toplam_kg"] * 100
            yon = "azalma" if delta < 0 else "artış"
            renk = PRIMARY if delta < 0 else TERRA
            st.markdown(
                f'<div class="banner">📈 {format_donem(onceki["period"])} dönemine göre toplamda '
                f'<strong style="color:{renk};">%{abs(delta):.1f} {yon}</strong> '
                f'({om["toplam_kg"]:,.0f} kg → {metrik["toplam_kg"]:,.0f} kg)</div>',
                unsafe_allow_html=True,
            )

    col_left, col_right = st.columns([1, 1])

    # Scope dağılımı
    with col_left:
        st.markdown('<div class="section-title">🎯 Scope Dağılımı</div>', unsafe_allow_html=True)
        scope_toplam = metrik["scope1_kg"] + metrik["scope2_kg"] + metrik["scope3_kg"]
        if scope_toplam > 0:
            s1 = metrik["scope1_kg"] / scope_toplam * 100
            s2 = metrik["scope2_kg"] / scope_toplam * 100
            s3 = metrik["scope3_kg"] / scope_toplam * 100
        else:
            s1 = s2 = s3 = 0

        for baslik, deger, pct, renk in [
            ("Scope 1 · Doğrudan Yakıtlar", metrik["scope1_kg"], s1, PRIMARY),
            ("Scope 2 · Elektrik", metrik["scope2_kg"], s2, PRIMARY2),
            ("Scope 3 · Gıda, Su, Atık, Kimyasal", metrik["scope3_kg"], s3, ACCENT),
        ]:
            st.markdown(f"""
            <div class="data-card" style="padding:14px 16px; margin:8px 0;">
              <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-size:13.5px;"><strong>{baslik}</strong></span>
                <span style="font-weight:800; color:{PRIMARY};">{deger:,.0f} kg</span>
              </div>
              <div style="background:{BORDER}; height:10px; border-radius:6px; overflow:hidden;">
                <div style="background:{renk}; width:{pct:.1f}%; height:100%;"></div>
              </div>
              <small style="color:{MUTED};">%{pct:.1f}</small>
            </div>
            """, unsafe_allow_html=True)

    # Grafik
    with col_right:
        st.markdown('<div class="section-title">📈 Kategori Dağılımı</div>', unsafe_allow_html=True)
        cats = list(scope["kategori_toplamlari"].keys())
        vals = list(scope["kategori_toplamlari"].values())
        aktif = [(c, v) for c, v in zip(cats, vals) if v > 0]
        if aktif:
            try:
                import plotly.express as px
                fig = px.pie(
                    names=[c for c, _ in aktif],
                    values=[v for _, v in aktif],
                    hole=0.45,
                    color_discrete_sequence=["#1d6b45", "#2e8b57", "#3da873", "#d99a3d", "#c0573d", "#7f9c6b"],
                )
                fig.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(t=10, b=10, l=0, r=0),
                    font=dict(family="Segoe UI", size=13),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                )
                fig.update_traces(textposition="inside", textinfo="percent")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Grafik oluşturulamadı: {e}")
        else:
            st.info("Grafik için yeterli veri yok.")

    st.markdown("---")

    # TEKİLLEŞTİRİLMİŞ KATEGORİ DETAYI
    st.markdown('<div class="section-title">🧾 Kategori & Alt Tür Detayları</div>', unsafe_allow_html=True)
    st.caption("Tüm tüketim ve emisyon verileri tek tabloda. TGA Tablo 10-13 çıktıları Excel/PDF dosyalarında yer alır.")

    detay_rows = []
    for kat, (emoji, birim) in {
        "Elektrik": ("🔌", "kWh"),
        "Doğal Gaz": ("🔥", "m³/kg"),
        "Su": ("🚿", "m³"),
        "Gıda Tüketimi": ("🍽️", "kg"),
        "Atık Yönetimi": ("♻️", "kg"),
        "Kimyasal Tüketimi": ("🧪", "L"),
    }.items():
        for alt_tur, miktar in tuketim.get(kat, {}).items():
            if not miktar or miktar <= 0:
                continue
            faktor = EMISSION_FACTORS.get(kat, {}).get(alt_tur, 0.0)
            emisyon = miktar * faktor
            pay = (emisyon / scope["toplam"] * 100) if scope["toplam"] > 0 else 0
            detay_rows.append({
                "Kategori": f"{emoji} {kat}",
                "Alt Tür": alt_tur,
                "Miktar": f"{miktar:,.1f} {birim}",
                "EF": faktor,
                "Emisyon (kg)": round(emisyon, 1),
                "Pay (%)": round(pay, 1),
            })

    if detay_rows:
        detay_df = pd.DataFrame(detay_rows).sort_values("Emisyon (kg)", ascending=False)
        st.dataframe(detay_df, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz emisyon kaynağı bulunmuyor.")

    # Öne çıkan kaynaklar
    st.markdown('<div class="section-title">⚠️ Öne Çıkan Emisyon Kaynakları</div>', unsafe_allow_html=True)
    if en_agir:
        cols = st.columns(min(3, len(en_agir)))
        for sira, ((kat, deger, yuzde), col) in enumerate(zip(en_agir, cols), 1):
            with col:
                st.markdown(f"""
                <div class="data-card" style="text-align:center; border-top:4px solid {_color_for_pct(yuzde)};">
                  <div style="font-size:12px; color:{MUTED}; margin-bottom:4px;">#{sira} KAYNAK</div>
                  <div style="font-weight:800; font-size:17px;">{kat}</div>
                  <div style="color:{PRIMARY}; font-weight:800; font-size:24px;">{deger:,.0f}</div>
                  <div style="color:{MUTED}; font-size:12px;">kg CO₂e · toplamın %{yuzde}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Henüz emisyon kaynağı bulunmuyor.")

    st.markdown("---")

    # İndirmeler
    st.markdown('<div class="section-title">📥 İndirmeler</div>', unsafe_allow_html=True)
    col_xls, col_pdf, col_yeni = st.columns(3)
    with col_xls:
        try:
            import openpyxl  # noqa: F401
            tablolar = tum_tablolar(r, period)
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for sheet, df in tablolar.items():
                    df.to_excel(writer, sheet_name=sheet[:31], index=False)
            st.download_button(
                label="📊 TGA Tabloları (Excel)",
                data=buffer.getvalue(),
                file_name=f"KarbonAT_{tesis['ad'].replace(' ', '_')}_{period}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except ImportError:
            st.warning("Excel için `openpyxl` kurun: pip install openpyxl")

    with col_pdf:
        try:
            green_pdf = save_green_report(r, period, onceki)
            st.download_button(
                label="🌿 Yeşil Rapor (PDF)",
                data=green_pdf,
                file_name=f"KarbonAT_YeşilRapor_{tesis['ad'].replace(' ', '_')}_{period}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF oluşturulamadı: {e}")

    with col_yeni:
        if st.button("🔄 Yeni Hesaplama", use_container_width=True):
            st.session_state.step = 2
            st.session_state.tuketim = _sifir_tuketim()
            st.rerun()

    st.markdown("---")

    # Geçmiş
    st.markdown('<div class="section-title">📅 Geçmiş Kayıtlar</div>', unsafe_allow_html=True)
    if st.session_state.history:
        kayit_df = pd.DataFrame([
            {
                "Dönem": format_donem(k["period"]),
                "Toplam (ton)": k["sonuc"]["metrikler"]["toplam_ton"],
                "Oda-Gün (kg)": k["sonuc"]["metrikler"]["oda_gun_kg"],
                "Müşteri (kg)": k["sonuc"]["metrikler"]["musteri_kg"],
                "m² (kg)": k["sonuc"]["metrikler"]["m2_aylik_kg"],
            }
            for k in st.session_state.history
        ])
        st.dataframe(kayit_df, use_container_width=True, hide_index=True)
        try:
            import plotly.express as px
            fig2 = px.line(kayit_df, x="Dönem", y="Toplam (ton)", markers=True,
                           color_discrete_sequence=[PRIMARY])
            fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                               margin=dict(t=10, b=10, l=0, r=0),
                               font=dict(family="Segoe UI", size=13))
            st.plotly_chart(fig2, use_container_width=True)
        except Exception:
            st.bar_chart(kayit_df.set_index("Dönem")["Toplam (ton)"])
    else:
        st.caption("Her aylık hesaplama otomatik olarak kaydedilir ve burada trend oluşur.")

    st.markdown(
        '<div class="footer">KarbonAT P2 · GSTC / TGA Uyumlu · v0.4</div>',
        unsafe_allow_html=True,
    )


# ==============================================
# ADIM 5 - İÇERİK MERKEZİ (İSKELET v1)
# ==============================================
def _icerik_karti(fac_id, tur):
    tur_id = tur["id"]
    defaults = varsayilan_tercih(tur_id)
    p = {**defaults, **(get_content_prefs(fac_id, tur_id) or {})}

    st.markdown(
        f'<div class="data-card" style="margin-top:10px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<div style="font-weight:800; font-size:16px;">{tur["emoji"]} {tur["baslik"]}</div>'
        f'<span class="chip" style="margin:0;">🚧 Planlama</span>'
        f'</div>'
        f'<p style="color:#6b7a70; font-size:13.5px; margin-top:8px;">{tur["aciklama"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander("🗂️ Planlanan Yapı (iskelet)", expanded=False):
        for i, baslik in enumerate(ISKELETLER[tur_id], 1):
            st.markdown(f"**{i}.** {baslik}", unsafe_allow_html=True)
        st.caption("Öneri taslaktır; araştırma tamamlandığında netleşir.")

    st.markdown('<div class="section-title">🎨 Tasarım Tercihleri</div>', unsafe_allow_html=True)
    for soru in tercih_sorulari(tur_id):
        secenekler = soru["secenekler"]
        idx = secenekler.index(p.get(soru["anahtar"])) if p.get(soru["anahtar"]) in secenekler else 0
        p[soru["anahtar"]] = st.selectbox(
            soru["soru"],
            secenekler,
            index=idx,
            key=f"tp_{fac_id}_{tur_id}_{soru['anahtar']}",
        )

    tema_keys = list(TEMALAR.keys())
    tema_adlar = [TEMALAR[k]["ad"] for k in tema_keys]
    tema_sec = st.selectbox(
        "Görsel Tema",
        tema_adlar,
        index=tema_keys.index(p["tema"]) if p["tema"] in tema_keys else 0,
        key=f"tp_{fac_id}_{tur_id}_tema",
        help="Üretim aşamasında rapor/broşür görsel paletine uygulanacak.",
    )
    p["tema"] = tema_keys[tema_adlar.index(tema_sec)]

    p["notlar"] = st.text_area(
        "✍️ AI'a tarzı / kapsamı anlat (isteğe bağlı)",
        value=p.get("notlar", ""),
        placeholder=("Örn: 'Sıcak ve samimi bir dille, sayılarla değil hikayelerle anlat. "
                     "Yenilenebilir enerjiye geçişimizi öne çıkar.'"),
        key=f"tp_{fac_id}_{tur_id}_notlar",
    )

    save_content_prefs(fac_id, tur_id, p)

    st.markdown("---")
    st.button(
        "🚧 Üret / İndir — Araştırma Aşamasında",
        disabled=True,
        use_container_width=True,
        key=f"uretim_{fac_id}_{tur_id}",
        help=("İçerik şablonu hazır değil; araştırma tamamlanınca "
              "(ileride AI destekli) buradan üretebileceksiniz."),
    )
    st.caption("Bu içerik türü şu an devre dışı. Tercihleriniz kaydedildi ve üretime hazır.")


def adim_icerik():
    tesis = st.session_state.tesis
    if not tesis or not tesis.get("id"):
        st.warning("Önce bir tesis seçin.")
        return

    st.markdown('<h1>🌿 İçerik Merkezi</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="chip">🌿 {tesis["ad"]}</div>'
        f'<div class="chip">🚧 Planlama Aşaması</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="banner">Buradan tüm sürdürülebilirlik içeriklerinizi tek panelden '
        'yapılandırırsınız: rapor, web sayfası, broşür, QR kart, politika, anket ve eğitim '
        'kayıtları. Şu anda <strong>planlama aşamasındayız</strong>: tasarım tercihlerinizi '
        'seçip kaydediyoruz; içerik metinleri araştırma tamamlanınca (ileride AI destekli) '
        'otomatik üretilecek.</div>',
        unsafe_allow_html=True,
    )

    # Türleri sekmelere grupla (anket -> alt sekmeler)
    gruplar = []
    for tur in ICERIK_TURLERI:
        if tur.get("grup"):
            mevcut = next((g for g in gruplar if g["id"] == tur["grup"]), None)
            if mevcut:
                mevcut["turler"].append(tur)
            else:
                gruplar.append({
                    "id": tur["grup"], "emoji": tur["emoji"], "baslik": tur["baslik"],
                    "turler": [tur],
                })
        else:
            gruplar.append({
                "id": tur["id"], "emoji": tur["emoji"], "baslik": tur["baslik"],
                "turler": [tur],
            })

    tabs = st.tabs([f'{g["emoji"]} {g["baslik"]}' for g in gruplar])
    for tab, g in zip(tabs, gruplar):
        with tab:
            if len(g["turler"]) == 1:
                _icerik_karti(tesis["id"], g["turler"][0])
            else:
                alt_tabs = st.tabs([t["alt_baslik"] for t in g["turler"]])
                for at, t in zip(alt_tabs, g["turler"]):
                    with at:
                        _icerik_karti(tesis["id"], t)

    st.markdown("---")
    if st.button("← Tesis Seçimine Dön", type="secondary"):
        st.session_state.step = 0
        st.rerun()


# ==============================================
# ROUTER
# ==============================================
if st.session_state.user is None:
    auth_screen()
else:
    sidebar()

    adimler = [
        adim_tesis_secimi,
        adim_tesis,
        adim_veri,
        adim_hesap,
        adim_sonuc,
        adim_icerik,
    ]

    adimler[st.session_state.step]()
