# ============================================
# KarbonAT - Yeşil Pazarlama Raporu (PDF)
# A3 Raporlama + A6 Doğru Tanıtım uyumlu, gerçek veriye dayalı iddialar
# ============================================

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit

from tga_tables import format_donem, tablo10_elektrik, tablo11_enerji, tablo12_su, tablo13_atik

# Font yükleme (önce tedarik edilmiş Roboto, sonra Windows Arial, sonrası Helvetica)
FONT_REG = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

def _yukle_font():
    """Roboto font'u tedarik edilen yollardan yükler (Linux/Mac/Windows)."""
    import os as _os
    candidate_dirs = [
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__))),  # projekökü
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data"),
    ]
    if _os.name == "nt":
        candidate_dirs.append(r"C:\Windows\Fonts")
    candidate_dirs.append("/usr/share/fonts")
    candidate_dirs.append("/usr/local/share/fonts")

    regular_paths = ["Roboto-Regular.ttf", "roboto/Roboto-Regular.ttf"]
    bold_paths = ["Roboto-Bold.ttf", "Roboto-Bold.otf", "roboto/Roboto-Bold.ttf"]

    def _bul(yol_listesi):
        for d in candidate_dirs:
            for alt in yol_listesi:
                p = _os.path.join(d, alt)
                if _os.path.isfile(p):
                    return p
        return None

    reg_p = _bul(regular_paths)
    bold_p = _bul(bold_paths)

    if reg_p:
        try:
            pdfmetrics.registerFont(TTFont('Roboto', reg_p))
            pdfmetrics.registerFontFamily('Roboto', normal='Roboto', bold='Roboto', italic='Roboto', boldItalic='Roboto')
            if bold_p:
                try:
                    pdfmetrics.registerFont(TTFont('Roboto-Bold', bold_p))
                    pdfmetrics.registerFontFamily('Roboto-Bold', normal='Roboto', bold='Roboto-Bold', italic='Roboto-Bold', boldItalic='Roboto-Bold')
                    return 'Roboto', 'Roboto-Bold'
                except Exception as e:
                    print(f"Roboto Bold yuklenemedi, normal kullanilacak: {e}")
                    return 'Roboto', 'Roboto'
            return 'Roboto', 'Roboto'
        except Exception as e:
            print(f"Roboto yuklenemedi: {e}")

    # Arial fallback (Windows)
    if _os.name == "nt":
        try:
            pdfmetrics.registerFont(TTFont('Arial', r'C:\Windows\Fonts\arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', r'C:\Windows\Fonts\arialbd.ttf'))
            return 'Arial', 'Arial-Bold'
        except Exception as e:
            pass

    return 'Helvetica', 'Helvetica-Bold'

FONT_REG, FONT_BOLD = _yukle_font()

PRIMARY = HexColor("#1b4332")
ACCENT = HexColor("#2d6a4f")
SOFT = HexColor("#40916c")
SAGE = HexColor("#95d5b2")
CREAM = HexColor("#f5f2ec")
INK = HexColor("#17201c")
LIGHT = HexColor("#6b7280")
WARN = HexColor("#e76f51")


def _kaydet(c, width):
    c.setFillColor(HexColor("#e7f0e6"))
    c.rect(0, 0, width, 1.2 * cm, fill=1, stroke=0)
    c.setFillColor(LIGHT)
    c.setFont(FONT_REG, 8)
    c.drawString(1.5 * cm, 0.5 * cm, "KarbonAT P2 - GSTC / TGA uyumlu sürdürülebilirlik raporu")
    c.drawRightString(width - 1.5 * cm, 0.5 * cm, "Gerçek tüketim verilerinden üretilmiştir")


def _pct_fark(yeni, onceki):
    if not onceki or onceki <= 0:
        return None
    return (yeni - onceki) / onceki * 100


def _fark_metni(delta_pct, azalt_pozitif=True):
    if delta_pct is None:
        return ""
    if azalt_pozitif:
        if delta_pct <= 0:
            return f"geçen aya göre %{-delta_pct:.1f} azalma"
        return f"geçen aya göre %{delta_pct:.1f} artış"
    if delta_pct >= 0:
        return f"geçen aya göre %{delta_pct:.1f} artış"
    return f"geçen aya göre %{-delta_pct:.1f} azalma"


def save_green_report(sonuc, period="", onceki=None):
    """
    sonuc: {tesis, statik, tuketim, scope, metrikler, en_agir}
    onceki: aynı yapıda önceki dönem kaydı (karşılaştırma için, opsiyonel)
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    tesis = sonuc.get("tesis") or {"ad": "Tesis", "m2": 0, "oda": 0, "personel": 0, "musteri": 0, "dolu_oda_gun": 0}
    metrik = sonuc.get("metrikler") or {"toplam_kg": 0, "toplam_ton": 0, "oda_gun_kg": 0, "m2_aylik_kg": 0, "musteri_kg": 0, "scope1_kg": 0, "scope2_kg": 0, "scope3_kg": 0}
    scope = sonuc.get("scope") or {"scope1": 0, "scope2": 0, "scope3": 0, "toplam": 0}
    _en = sonuc.get("en_agir", [])
    # en_agir her türlü şekle karşı dayanıklı hale getir
    en_agir = []
    if isinstance(_en, dict):
        # dict ise {kat: deger} şeklinde
        try:
            en_agir = [(k, float(v), 0) for k, v in _en.items()]
        except Exception:
            en_agir = []
    elif isinstance(_en, (list, tuple)):
        tmp = []
        for el in _en:
            if isinstance(el, (list, tuple)) and len(el) >= 2:
                try:
                    kat = str(el[0])
                    deger = float(el[1]) if el[1] is not None else 0.0
                    yuzde = float(el[2]) if len(el) > 2 and el[2] is not None else 0.0
                    tmp.append((kat, deger, yuzde))
                except Exception:
                    continue
            elif isinstance(el, dict):
                try:
                    for k, v in el.items():
                        tmp.append((str(k), float(v), 0))
                except Exception:
                    continue
        en_agir = tmp
    tuketim = sonuc.get("tuketim") or {}

    # onceki: hem record dict hem sonuc dict hem de bozuk int gelebilir — hepsini normalize et
    if isinstance(onceki, dict) and "sonuc" in onceki and isinstance(onceki["sonuc"], dict):
        onceki = onceki["sonuc"]
    if not isinstance(onceki, dict):
        onceki = {}
    # tesis/metrik/scope int gelirse dict'e çevir
    if not isinstance(tesis, dict):
        tesis = {"ad": str(tesis) if tesis else "Tesis", "m2": 0, "oda": 0, "personel": 0, "musteri": 0, "dolu_oda_gun": 0}
    if not isinstance(metrik, dict):
        metrik = {"toplam_kg": 0, "toplam_ton": 0, "oda_gun_kg": 0, "m2_aylik_kg": 0, "musteri_kg": 0, "scope1_kg": 0, "scope2_kg": 0, "scope3_kg": 0}
    if not isinstance(scope, dict):
        scope = {"scope1": 0, "scope2": 0, "scope3": 0, "toplam": 0}
    if not isinstance(tuketim, dict):
        tuketim = {}

    donem = format_donem(period)
    onceki_metrik = onceki.get("metrikler") if isinstance(onceki, dict) else None
    if not isinstance(onceki_metrik, dict):
        onceki_metrik = None

    # ===== BAŞLIK =====
    c.setFillColor(PRIMARY)
    c.rect(0, height - 3.4 * cm, width, 3.4 * cm, fill=1, stroke=0)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(FONT_BOLD, 21)
    c.drawString(1.5 * cm, height - 1.7 * cm, "SÜRDÜRÜLEBİLİRLİK RAPORU")
    c.setFont(FONT_REG, 11)
    c.drawString(1.5 * cm, height - 2.5 * cm, f"{tesis['ad']}  |  {donem}")
    c.setFillColor(SAGE)
    c.setFont(FONT_BOLD, 9)
    c.drawRightString(width - 1.5 * cm, height - 1.7 * cm, "KarbonAT P2")

    y = height - 4.6 * cm

    # ===== TAZE İDDİA BANDI (A6: veriye dayalı) =====
    toplam_kg = metrik["toplam_kg"]
    toplam_ton = metrik["toplam_ton"]
    kisi_basi = metrik.get("musteri_kg", 0)

    c.setFillColor(CREAM)
    c.rect(1.5 * cm, y - 0.4 * cm, width - 3 * cm, 1.6 * cm, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(1.5 * cm, y - 0.4 * cm, 0.18 * cm, 1.6 * cm, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 12)
    c.drawString(2.0 * cm, y + 0.75 * cm, "Bu ay kaydedilen karbon ayak izi")
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 16)
    c.drawString(2.0 * cm, y + 0.2 * cm, f"{toplam_ton} ton CO₂e  ({toplam_kg:,.0f} kg)")
    c.setFillColor(LIGHT)
    c.setFont(FONT_REG, 9)
    c.drawRightString(width - 2.0 * cm, y + 0.3 * cm,
                      f"Kişi başı: {kisi_basi} kg CO₂e / misafir")
    y -= 2.5 * cm

    # ===== KPI KARTLARI =====
    kpi_data = [
        ("TOPLAM", f"{toplam_ton} ton CO₂e", "Aylık toplam"),
        ("ODA-GÜN", f"{metrik['oda_gun_kg']} kg", "HCMI birincil metrik"),
        ("METREKARE", f"{metrik['m2_aylik_kg']} kg", "m² başına aylık"),
        ("MÜŞTERİ", f"{metrik['musteri_kg']} kg", "Kişi başına"),
    ]
    box_w = (width - 3 * cm - 0.6 * cm) / 4
    box_h = 2.0 * cm
    box_y = y - box_h
    for i, (label, value, sub) in enumerate(kpi_data):
        x = 1.5 * cm + i * (box_w + 0.2 * cm)
        c.setFillColor(CREAM)
        c.rect(x, box_y, box_w, box_h, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.rect(x, box_y, 0.12 * cm, box_h, fill=1, stroke=0)
        c.setFillColor(LIGHT)
        c.setFont(FONT_REG, 7)
        c.drawString(x + 0.3 * cm, box_y + box_h - 0.5 * cm, label)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 12)
        c.drawString(x + 0.3 * cm, box_y + 1.0 * cm, value)
        c.setFillColor(ACCENT)
        c.setFont(FONT_REG, 7.5)
        c.drawString(x + 0.3 * cm, box_y + 0.35 * cm, sub)
    y = box_y - 1.1 * cm

    # ===== YEŞİL GÖSTERGELER + DEĞİŞİM (geçmiş karşılaştırma) =====
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(1.5 * cm, y, "Yeşil Göstergeler")
    y -= 0.75 * cm

    def _kaynak_toplami(kategori):
        if isinstance(kategori, dict):
            return sum(v for v in kategori.values() if v and v > 0)
        return sum(v for v in tuketim.get(kategori, {}).values() if v and v > 0)

    su_m3 = _kaynak_toplami("Su")
    atik_kg = _kaynak_toplami("Atık Yönetimi")
    atik_df = tablo13_atik(tuketim)
    geri_oran = 0.0
    if not atik_df.empty:
        toplam_atik = sum(atik_df["Miktar (kg)"])
        geri = sum(r["Miktar (kg)"] for _, r in atik_df.iterrows()
                   if r["Bertaraf Yöntemi"] in ("Geri dönüşüm", "Kompost / biyolojik"))
        if toplam_atik > 0:
            geri_oran = geri / toplam_atik * 100

    _onceki_tuk = onceki.get("tuketim", {}) if isinstance(onceki, dict) else {}
    if not isinstance(_onceki_tuk, dict):
        _onceki_tuk = {}
    _onceki_su_dict = _onceki_tuk.get("Su", {})
    if not isinstance(_onceki_su_dict, dict):
        _onceki_su_dict = {}
    onceki_su = _kaynak_toplami(_onceki_su_dict) if onceki else 0

    gosterge_rows = [
        ("CO₂ / Misafir", f"{metrik['musteri_kg']} kg/misafir",
         _fark_metni(_pct_fark(metrik['musteri_kg'], (onceki_metrik or {}).get('musteri_kg')))),
        ("Su Tüketimi", f"{su_m3:,.1f} m³",
         _fark_metni(_pct_fark(su_m3, onceki_su))),
        ("Geri Kazanılan Atık", f"%{geri_oran:.1f}", ""),
    ]

    for baslik, deger, fark in gosterge_rows:
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 9)
        c.drawString(1.5 * cm, y, baslik)
        c.setFillColor(PRIMARY)
        c.setFont(FONT_BOLD, 9)
        c.drawRightString(width - 5 * cm, y, deger)
        c.setFillColor(ACCENT if fark else LIGHT)
        c.setFont(FONT_REG, 8)
        c.drawRightString(width - 1.5 * cm, y, fark or "-")
        y -= 0.55 * cm
    y -= 0.4 * cm

    # ===== SCOPE DAĞILIMI =====
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(1.5 * cm, y, "Emisyon Dağılımı (Scope)")
    y -= 0.75 * cm
    scope_total = scope.get("toplam", 0) or 1
    for baslik, deger in [
        ("Scope 1 - Doğrudan yakıtlar", scope.get("scope1", 0)),
        ("Scope 2 - Elektrik", scope.get("scope2", 0)),
        ("Scope 3 - Gıda, su, atık, kimyasal", scope.get("scope3", 0)),
    ]:
        pct = deger / scope_total * 100
        c.setFillColor(INK)
        c.setFont(FONT_REG, 9)
        c.drawString(1.5 * cm, y, baslik)
        c.setFillColor(ACCENT)
        c.setFont(FONT_BOLD, 9)
        c.drawRightString(width - 1.5 * cm, y, f"{deger:,.0f} kg  (%{pct:.1f})")
        y -= 0.5 * cm
    y -= 0.5 * cm

    # ===== EN AĞIR KAYNAKLAR =====
    if y > 7 * cm and en_agir:
        c.setFillColor(PRIMARY)
        c.setFont(FONT_BOLD, 12)
        c.drawString(1.5 * cm, y, "Öne Çıkan Emisyon Kaynakları")
        y -= 0.6 * cm
        for sira, (kat, deger, yuzde) in enumerate(en_agir[:3], 1):
            if y < 4 * cm:
                break
            c.setFillColor(HexColor("#fdf6ee"))
            c.rect(1.5 * cm, y - 0.2 * cm, width - 3 * cm, 0.7 * cm, fill=1, stroke=0)
            c.setFillColor(WARN)
            c.rect(1.5 * cm, y - 0.2 * cm, 0.15 * cm, 0.7 * cm, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont(FONT_BOLD, 9)
            c.drawString(2 * cm, y + 0.15 * cm, f"{sira}. {kat}")
            c.setFillColor(LIGHT)
            c.setFont(FONT_REG, 8)
            c.drawString(2 * cm, y - 0.1 * cm, f"Toplamın %{yuzde:.1f}'i")
            c.setFillColor(PRIMARY)
            c.setFont(FONT_BOLD, 9)
            c.drawRightString(width - 1.5 * cm, y + 0.15 * cm, f"{deger:,.0f} kg CO₂e")
            y -= 0.85 * cm

    y -= 0.5 * cm

    # ===== DİPNOT (A6 doğru tanıtım) =====
    if y < 4 * cm:
        c.showPage()
        y = height - 2.5 * cm

    notlar = [
        "Bu rapor KarbonAT P2 tarafından, tesisin gerçek aylık tüketim verilerinden otomatik üretilmiştir.",
        "Tüm yeşil iddialar bu rapordaki ölçülen verilere dayanmaktadır (GSTC A6 - Doğru Tanıtım).",
        "Türkiye şebeke elektriği emisyon faktörü 0,478 kgCO₂e/kWh kullanılmıştır (TEİAş/EPDK).",
        "Oda-gün ve misafir başına metrikler HCMI endüstri standardına göre hesaplanmıştır.",
    ]
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 10)
    c.drawString(1.5 * cm, y, "Hesaplama Yöntemi & Doğruluk")
    y -= 0.5 * cm
    c.setFillColor(LIGHT)
    c.setFont(FONT_REG, 8.5)
    for not_ in notlar:
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            _kaydet(c, width)
        for line in simpleSplit(not_, FONT_REG, 8.5, width - 3 * cm):
            c.drawString(1.5 * cm, y, "• " + line)
            y -= 0.35 * cm

    _kaydet(c, width)
    c.showPage()
    y = height - 2.5 * cm

    # ===== 2. SAYFA: YÖNETİCİ ÖZETİ & YOL HARİTASI (ön analiz) =====
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 15)
    c.drawString(1.5 * cm, y, "Yönetici Özeti & Yol Haritası")
    y -= 0.55 * cm
    c.setFillColor(LIGHT)
    c.setFont(FONT_REG, 8.5)
    for line in simpleSplit("Bu sayfa ilk sayfanın ön analizi niteliğindedir. TGA Tablo 10-13 ham verileri denetime hazır Excel ekinde sunulur; burada yalnızca özet ve aksiyon önerileri yer alır.", FONT_REG, 8.5, width - 3*cm):
        c.drawString(1.5 * cm, y, line)
        y -= 0.34 * cm
    y -= 0.2 * cm

    # --- Bu ayın hikayesi (2 cumle) ---
    hikaye = f"{tesis['ad']} bu ay {toplam_ton} ton CO₂e üretti. "
    if onceki_metrik and onceki_metrik.get("toplam_kg"):
        delta = (metrik["toplam_kg"] - onceki_metrik["toplam_kg"]) / onceki_metrik["toplam_kg"]*100
        yon = "azalış" if delta < 0 else "artış"
        hikaye += f"Geçen aya göre %{abs(delta):.1f} {yon} var. "
    if en_agir:
        ilk = en_agir[0]
        # en_agir tuple (kat,deger,yuzde)
        kat0 = ilk[0] if isinstance(ilk, (list,tuple)) else str(ilk)
        hikaye += f"En büyük pay {kat0} kaynaklı."
    c.setFillColor(CREAM)
    c.rect(1.5*cm, y - 1.15*cm, width -3*cm, 1.35*cm, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(1.5*cm, y - 1.15*cm, 0.14*cm, 1.35*cm, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(FONT_REG, 8.5)
    ty = y - 0.35*cm
    for line in simpleSplit(hikaye, FONT_REG, 8.5, width - 4*cm):
        c.drawString(2.05*cm, ty, line)
        ty -= 0.33*cm
        if ty < 3*cm:
            break
    y -= 1.6*cm

    # --- Önerilen aksiyonlar (en_agir'a göre) ---
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 11)
    c.drawString(1.5*cm, y, "Öncelikli Aksiyon Önerileri")
    y -= 0.5*cm
    # Harita: kategori -> öneri
    ONERI_HARITA = {
        "Elektrik": "LED & sensör dönüşümü, YEK-G sertifikalı tedarik, çatı PV fizibilitesi",
        "Doğal Gaz": "Kazan verimliliği, ısı geri kazanım, yalıtım kontrolü",
        "Su": "Akıllı sayaç, havuz sızıntı kontrolü, misafir bilgilendirme kartı",
        "Atık": "Kaynağında ayrıştırma kutuları, personel eğitimi, tartım fişi rutini",
        "Gıda": "Yerel/m evsimsel menü, porsiyon optimizasyonu, atık tartımı",
        "Kimyasal": "Konsantre/dozlama sistemi, eko-etiketli ürün geçişi",
        "Soğutucu": "Kaçak kontrol, düşük GWP gaz geçişi, bakım logu",
        "Araç": "Rota optimizasyonu, filo bakımı, toplu transfer teşviki",
    }
    aksiyonlar = []
    for kat, _, _ in (en_agir[:3] if en_agir else []):
        # kategori adından anahtar bul
        ana = next((k for k in ONERI_HARITA if k.lower() in kat.lower()), None)
        if ana:
            aksiyonlar.append(f"{kat}: {ONERI_HARITA[ana]}")
        else:
            aksiyonlar.append(f"{kat}: Ölçüm sıklığını artır, sapmayı haftalık izle")
    if not aksiyonlar:
        aksiyonlar = ["Veri girişini düzenli yap – 12 ay trendi otomatik oluşur.", "Tablo 6 ekip sorumluluklarını aylık gözden geçir.", "Misafir anketini (Tablo5) aktif tut."]
    for idx, met in enumerate(aksiyonlar, 1):
        if y < 3.5*cm:
            c.showPage()
            y = height - 2.5*cm
            _kaydet(c, width)
        c.setFillColor(HexColor("#f6faf7"))
        c.rect(1.5*cm, y -0.22*cm, width-3*cm, 0.68*cm, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.setFont(FONT_BOLD, 8.5)
        c.drawString(1.7*cm, y+0.12*cm, f"{idx}.")
        c.setFillColor(INK)
        c.setFont(FONT_REG, 8.2)
        # wrap
        lines = simpleSplit(met, FONT_REG, 8.2, width-4.2*cm)
        c.drawString(2.1*cm, y+0.12*cm, lines[0] if lines else met)
        if len(lines) > 1:
            c.drawString(2.1*cm, y-0.16*cm, lines[1])
        y -= 0.82*cm
    y -= 0.15*cm

    # --- Kompakt TGA özet tabloları (3 mini tablo, header corpora) ---
    # Basit manuel mini tablo cizimi – 3'er satir, sığar garantili
    def _mini_tablo(baslik, df, cols, ypos):
        if ypos < 4.2*cm:
            c.showPage()
            ypos = height - 2.5*cm
            _kaydet(c, width)
        c.setFillColor(ACCENT)
        c.setFont(FONT_BOLD, 9)
        c.drawString(1.5*cm, ypos, baslik)
        ypos -= 0.45*cm
        # header arkaplan
        c.setFillColor(PRIMARY)
        c.rect(1.5*cm, ypos-0.08*cm, width-3*cm, 0.48*cm, fill=1, stroke=0)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont(FONT_BOLD, 7)
        for j, col in enumerate(cols):
            x = 1.5*cm + j*((width-3*cm)/len(cols))
            c.drawString(x+0.08*cm, ypos+0.12*cm, col)
        ypos -= 0.48*cm
        # rows (max 3 + TOPLAM)
        rows = []
        if df is not None and not df.empty:
            # TOPLAM hariç en büyük 2 + TOPLAM
            tmp = df.copy()
            # TOPLAM satiri sonda ise ayir
            toplam_row = None
            if not tmp.empty and str(tmp.iloc[-1].iloc[0]).upper() == "TOPLAM":
                toplam_row = tmp.iloc[-1]
                tmp = tmp.iloc[:-1]
            # en büyük emisyon'a göre sırala (son sütun genelde emisyon)
            try:
                tmp = tmp.sort_values(tmp.columns[-1], ascending=False).head(2)
            except Exception:
                tmp = tmp.head(2)
            if toplam_row is not None:
                # birlestir
                import pandas as pd
                rows_df = pd.concat([tmp, toplam_row.to_frame().T], ignore_index=True)
            else:
                rows_df = tmp
            for _, r in rows_df.iterrows():
                rows.append([str(r[col]) if col in r else "" for col in cols])
        # zebra rows
        for ri, r in enumerate(rows):
            if ypos < 2.2*cm:
                c.showPage()
                ypos = height - 2.5*cm
                _kaydet(c, width)
            fill = HexColor("#ffffff") if ri%2==0 else HexColor("#eef4ee")
            c.setFillColor(fill)
            c.rect(1.5*cm, ypos-0.06*cm, width-3*cm, 0.42*cm, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont(FONT_REG, 7)
            for j, val in enumerate(r):
                x = 1.5*cm + j*((width-3*cm)/len(cols))
                # sayi ise saga, metin sola
                txt = val
                if len(txt) > 22:
                    txt = txt[:21] + "…"
                c.drawString(x+0.08*cm, ypos+0.10*cm, txt)
            # grid cizgisi
            c.setStrokeColor(HexColor("#cfd8cf"))
            c.setLineWidth(0.35)
            c.rect(1.5*cm, ypos-0.06*cm, width-3*cm, 0.42*cm, fill=0, stroke=1)
            ypos -= 0.42*cm
        return ypos - 0.18*cm

    y = _mini_tablo("Tablo 10 – Elektrik (özet)", tablo10_elektrik(tuketim), ["Alt Tür","Tüketim (kWh)","Emisyon (kgCO₂e)"], y)
    y = _mini_tablo("Tablo 12 – Su (özet)", tablo12_su(tuketim, tesis.get("dolu_oda_gun",0), tesis.get("musteri",0)), ["Kaynak","Tüketim (m³)","Oda-Gün Başına (L)"], y)
    y = _mini_tablo("Tablo 13 – Atık (özet)", tablo13_atik(tuketim), ["Atık Türü","Miktar (kg)","Emisyon (kgCO₂e)"], y)

    # Dip not – Excel eki vurgusu
    if y < 3*cm:
        c.showPage()
        y = height - 2.5*cm
        _kaydet(c, width)
    c.setFillColor(LIGHT)
    c.setFont(FONT_REG, 7.5)
    for line in simpleSplit("Not: Tam TGA Tablo 10-13 ham verileri ve Tablo 6-7, kimyasal envanter denetime hazır Excel ekinde sunulur. Bu PDF yönetici özetidir.", FONT_REG, 7.5, width-3*cm):
        c.drawString(1.5*cm, y, line)
        y -= 0.32*cm

    _kaydet(c, width)
    c.save()
    buffer.seek(0)
    return buffer
