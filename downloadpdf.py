# ============================================
# KarbonAT P2 - PDF Rapor Üreticisi (Temiz Versiyon)
# Windows Arial fontu kullanır - Türkçe karakterler sorunsuz basılır.
# ============================================

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import textwrap

# Font yükleme (Windows Arial)
FONT_REG = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

try:
    pdfmetrics.registerFont(TTFont('Arial', r'C:\Windows\Fonts\arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', r'C:\Windows\Fonts\arialbd.ttf'))
    FONT_REG = 'Arial'
    FONT_BOLD = 'Arial-Bold'
except Exception as e:
    print(f"Arial yüklenemedi, Helvetica'ye düşüldü: {e}")

# Marka renkleri
PRIMARY = HexColor("#668c2b")
ACCENT  = HexColor("#78a633")
SOFT    = HexColor("#8ea66a")
CREAM   = HexColor("#f2f2f2")
INK     = HexColor("#0d0d0d")
LIGHT   = HexColor("#888888")


def _draw_header(c, width, height):
    c.setFillColor(PRIMARY)
    c.rect(0, height - 2.8 * cm, width, 2.8 * cm, fill=1, stroke=0)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(FONT_BOLD, 22)
    c.drawString(1.5 * cm, height - 1.7 * cm, "KarbonAT P2")
    c.setFont(FONT_REG, 11)
    c.drawString(1.5 * cm, height - 2.4 * cm, "GSTC Uyumlu Karbon Ayak İzi Raporu")


def _draw_footer(c, width):
    c.setFillColor(CREAM)
    c.rect(0, 0, width, 1.2 * cm, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(FONT_REG, 8)
    c.drawString(1.5 * cm, 0.5 * cm, "KarbonAT P2 - GSTC Uyumlu Karbon Hesaplama")
    c.drawRightString(width - 1.5 * cm, 0.5 * cm, "KarbonAT P2 · v0.2")


def _draw_kpi_card(c, x, y, w, h, label, value, sub):
    c.setFillColor(CREAM)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setFillColor(PRIMARY)
    c.rect(x, y, 0.15 * cm, h, fill=1, stroke=0)
    c.setFillColor(LIGHT)
    c.setFont(FONT_REG, 7)
    c.drawString(x + 0.3 * cm, y + h - 0.4 * cm, label)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 13)
    c.drawString(x + 0.3 * cm, y + 0.7 * cm, value)
    c.setFillColor(ACCENT)
    c.setFont(FONT_REG, 7.5)
    c.drawString(x + 0.3 * cm, y + 0.3 * cm, sub)


def save_as_pdf(sonuc):
    """sonuc = {tesis, statik, tuketim, scope, metrikler, en_agir}"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    _draw_header(c, width, height)
    y = height - 4 * cm

    tesis = sonuc["tesis"]
    statik = sonuc["statik"]
    metrik = sonuc["metrikler"]
    scope = sonuc["scope"]
    en_agir = sonuc["en_agir"]

    # Tesis bilgisi
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 17)
    c.drawString(1.5 * cm, y, tesis["ad"])
    y -= 0.8 * cm

    c.setFillColor(INK)
    c.setFont(FONT_REG, 10)
    c.drawString(1.5 * cm, y,
        f"Dönem: {tesis['donem'].strftime('%B %Y')}  |  "
        f"{tesis['oda']} oda  |  {tesis['m2']} m²  |  "
        f"{tesis['personel']} personel  |  {tesis['musteri']} müşteri")
    y -= 0.5 * cm
    c.drawString(1.5 * cm, y,
        f"Dolu oda-gün: {tesis['dolu_oda_gun']}  |  "
        f"Yenilenebilir Enerji Oranı: %{statik['yenilenebilir']}")
    y -= 0.8 * cm

    # KPI kartları
    kpi_data = [
        ("TOPLAM EMİSYON", f"{metrik['toplam_ton']} ton CO₂e", "Aylık toplam"),
        ("ODA-GÜN", f"{metrik['oda_gun_kg']} kg CO₂e", "HCMI birincil metrik"),
        ("METREKARE", f"{metrik['m2_aylik_kg']} kg CO₂e", "Aylık, m² başına"),
        ("MÜŞTERİ", f"{metrik['musteri_kg']} kg CO₂e", "Kişi başına"),
    ]
    box_w = (width - 3 * cm - 0.6 * cm) / 4
    box_h = 2.0 * cm
    box_y = y - box_h
    for i, (label, value, sub) in enumerate(kpi_data):
        x = 1.5 * cm + i * (box_w + 0.2 * cm)
        _draw_kpi_card(c, x, box_y, box_w, box_h, label, value, sub)
    y = box_y - 1.0 * cm

    # Scope dağılımı
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(1.5 * cm, y, "Scope Dağılımı")
    y -= 0.7 * cm

    scope_total = metrik["scope1_kg"] + metrik["scope2_kg"] + metrik["scope3_kg"]
    scope_items = [
        ("Scope 1 - Doğrudan Yakıtlar", metrik["scope1_kg"]),
        ("Scope 2 - Elektrik", metrik["scope2_kg"]),
        ("Scope 3 - Diğer", metrik["scope3_kg"]),
    ]
    for baslik, deger in scope_items:
        pct = (deger / scope_total * 100) if scope_total > 0 else 0
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 9)
        c.drawString(1.5 * cm, y, baslik)
        c.setFillColor(PRIMARY)
        c.setFont(FONT_BOLD, 9)
        c.drawRightString(width - 1.5 * cm, y, f"{deger:,.0f} kg CO₂e  (%{pct:.1})")
        y -= 0.5 * cm
    y -= 0.3 * cm

    # Kategori dağılımı tablosu (renkli bar yok, sadece metin)
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(1.5 * cm, y, "Kategoriye Göre Dağılım")
    y -= 0.7 * cm

    toplam_kg = scope["toplam"]
    if toplam_kg > 0:
        kategori_sirali = sorted(scope["kategori_toplamlari"].items(), key=lambda x: x[1], reverse=True)
        for kat, deger in kategori_sirali:
            yuzde = (deger / toplam_kg * 100)
            if yuzde > 40:
                renk = HexColor("#d97706")
            elif yuzde > 20:
                renk = PRIMARY
            elif yuzde > 10:
                renk = SOFT
            else:
                renk = HexColor("#c7dd93")

            # Renkli daire (kategorinin emisyon oranına göre boyutlandırılmış)
            max_dot = 1.2 * cm
            dot_d = max(0.3 * cm, min(max_dot, (yuzde / 100) * max_dot))
            c.setFillColor(renk)
            c.circle(2 * cm, y + 0.1 * cm, dot_d / 2, fill=1, stroke=0)

            c.setFillColor(INK)
            c.setFont(FONT_REG, 9)
            c.drawString(3.5 * cm, y, kat)
            c.setFillColor(PRIMARY)
            c.setFont(FONT_BOLD, 9)
            c.drawRightString(width - 3.5 * cm, y, f"{deger:,.0f} kg")
            c.setFillColor(LIGHT)
            c.setFont(FONT_REG, 8)
            c.drawRightString(width - 1.5 * cm, y, f"%{yuzde:.1}")
            y -= 0.6 * cm

    y -= 0.3 * cm

    # Öne çıkan kaynaklar
    if y > 6 * cm:
        c.setFillColor(PRIMARY)
        c.setFont(FONT_BOLD, 12)
        c.drawString(1.5 * cm, y, "Öne Çıkan Emisyon Kaynakları")
        y -= 0.6 * cm

    for sira, (kat, deger, yuzde) in enumerate(en_agir[:3], 1):
        if y < 4 * cm:
            break
        c.setFillColor(HexColor("#fffbeb"))
        c.rect(1.5 * cm, y - 0.2 * cm, width - 3 * cm, 0.7 * cm, fill=1, stroke=0)
        c.setFillColor(HexColor("#f59e0b"))
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

    # Hesaplama yöntemi (alta dipsöz)
    y -= 0.5 * cm
    if y < 3 * cm:
        c.showPage()
        y = height - 2 * cm
        _draw_footer(c, width)

    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 10)
    c.drawString(1.5 * cm, y, "Hesaplama Yöntemi")
    y -= 0.5 * cm

    notlar = [
        "Türkiye şebeke elektriği emisyon faktörü 0,478 kgCO₂e/kWh olarak kullanılmıştır.",
        "Scope 1: Tesis bünyesinde yakılan fosil yakıtlar.",
        "Scope 2: Şebekeden satın alınan elektrik (YEK-G sertifikalı kısım sıfır emisyon).",
        "Scope 3: Gıda tedarik zinciri, atık bertarafı, su arıtma, kimyasal üretim.",
        "Oda-gün, müşteri ve m² metrikleri HCMI endüstri standardından alınmıştır.",
    ]
    c.setFillColor(INK)
    c.setFont(FONT_REG, 8.5)
    for not_ in notlar:
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            _draw_footer(c, width)
        wrapped = textwrap.wrap(not_, width=95)
        for line in wrapped:
            c.drawString(1.5 * cm, y, "• " + line)
            y -= 0.32 * cm

    _draw_footer(c, width)
    c.save()
    buffer.seek(0)
    return buffer
