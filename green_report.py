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

from tga_tables import format_donem, tablo10_elektrik, tablo12_su, tablo13_atik

# Font yükleme (Windows Arial - Türkçe karakterler)
FONT_REG = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
try:
    pdfmetrics.registerFont(TTFont('Arial', r'C:\Windows\Fonts\arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', r'C:\Windows\Fonts\arialbd.ttf'))
    FONT_REG = 'Arial'
    FONT_BOLD = 'Arial-Bold'
except Exception as e:
    print(f"Arial yüklenemedi, Helvetica'ye düşüldü: {e}")

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

    tesis = sonuc["tesis"]
    metrik = sonuc["metrikler"]
    scope = sonuc["scope"]
    en_agir = sonuc.get("en_agir", [])
    tuketim = sonuc["tuketim"]

    donem = format_donem(period)
    onceki_metrik = (onceki or {}).get("metrikler")

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

    onceki_su = _kaynak_toplami((onceki or {}).get("tuketim", {}).get("Su", {})) if onceki else 0

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

    # ===== 2. SAYFA: TGA TAKİP TABLOLARI =====
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 15)
    c.drawString(1.5 * cm, y, "TGA Takip Tabloları (Veri Kaydı)")
    y -= 0.7 * cm
    c.setFillColor(LIGHT)
    c.setFont(FONT_REG, 9)
    c.drawString(1.5 * cm, y, "Aşağıdaki tablolar TGA Tablo 10-13 formatına uygun olarak üretilmiştir.")
    y -= 0.8 * cm

    tablolar = [
        ("Tablo 10 - Elektrik Tüketimi", tablo10_elektrik(tuketim), ["Alt Tür", "Tüketim (kWh)", "Emisyon (kgCO₂e)"]),
        ("Tablo 12 - Su Sarfiyatı", tablo12_su(tuketim, tesis.get("dolu_oda_gun", 0), tesis.get("musteri", 0)), ["Kaynak", "Tüketim (m³)", "Oda-Gün Başına (L)"]),
        ("Tablo 13 - Katı Atık", tablo13_atik(tuketim), ["Atık Türü", "Miktar (kg)", "Emisyon (kgCO₂e)"]),
    ]

    for baslik, df, cols in tablolar:
        if y < 4 * cm:
            c.showPage()
            y = height - 2.5 * cm
        c.setFillColor(ACCENT)
        c.setFont(FONT_BOLD, 11)
        c.drawString(1.5 * cm, y, baslik)
        y -= 0.5 * cm

        rows = []
        if not df.empty:
            rows = df[[c for c in df.columns if c in cols]].tail(8).values.tolist()

        c.setFillColor(PRIMARY)
        c.setFont(FONT_BOLD, 8)
        for j, col in enumerate(cols):
            x = 1.5 * cm + j * ((width - 3 * cm) / len(cols))
            c.drawString(x, y, col)
        y -= 0.35 * cm

        c.setFillColor(INK)
        c.setFont(FONT_REG, 8)
        for r in rows:
            if y < 2 * cm:
                c.showPage()
                y = height - 2 * cm
            for j, val in enumerate(r):
                x = 1.5 * cm + j * ((width - 3 * cm) / len(cols))
                c.drawString(x, y, f"{val:,.2f}" if isinstance(val, (int, float)) else str(val))
            y -= 0.32 * cm
        y -= 0.5 * cm

    _kaydet(c, width)
    c.save()
    buffer.seek(0)
    return buffer
