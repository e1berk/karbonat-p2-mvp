# ============================================
# KarbonAT - RAPORLAR (raporlama alt sistemi)
#
# Kullanıcının referans-sablonlari/ olarak attığı TGA formatlarının
# HER BİRİ ayrı bir şablondur. AI şablonları verilere göre AYRI AYRI
# doldurur; deterministik olanlar (Tablo 10-13) kodla üretilir.
# Üretilen raporlar data_store üzerinden dönem bazında kaydedilir
# (profil -> raporlar -> aylar).
# ============================================
from __future__ import annotations

import os
import re
from io import BytesIO

import pandas as pd

# Deterministik tablo üreticileri
from tga_tables import (
    tablo10_elektrik,
    tablo11_enerji,
    tablo12_su,
    tablo13_atik,
    kimyasal_envanter,
)

RAPOR_SABLONLARI = [
    {
        "id": "tablo1",
        "emoji": "⚠️",
        "baslik": "Risk Analizi (Tablo 1)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Tablo 1"],
        "aciklama": "Risk matrisi formatında tesis risklerini veriyle ilişkilendirir; olasılık/etki skorları önerir.",
    },
    {
        "id": "tablo2",
        "emoji": "🎯",
        "baslik": "Hedefler (Tablo 2)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Tablo 2"],
        "aciklama": "TGA Tablo 2 formatında ölçülebilir sürdürülebilirlik hedefleri; mevcut veriye dayalı baz + hedef.",
    },
    {
        "id": "tablo3",
        "emoji": "⚖️",
        "baslik": "Yasal Uygunluk & Yükümlülükler (Tablo 3)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Tablo 3"],
        "aciklama": "Çevre ve turizm mevzuatına uygunluk listesi; ilgili yükümlülükleri ve uyum durumu.",
    },
    {
        "id": "anlati",
        "emoji": "📄",
        "baslik": "Sürdürülebilirlik Raporu (Tablo 4)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Raporlamasi", "Politika"],
        "aciklama": "TGA Tablo 4 formatında, tesis verileriyle doldurulmuş anlatı raporu; yönetim mesajı, performans, hedefler ve uyum maddeleri.",
    },
    {
        "id": "tablo5",
        "emoji": "📊",
        "baslik": "Misafir Anketi Soruları (Tablo 5)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Tablo 5"],
        "aciklama": "TGA Tablo 5 sürdürülebilirlik anketi soru seti; tesise uyarlanmış memnuniyet + farkındalık soruları.",
    },
    {
        "id": "tablo7",
        "emoji": "🤝",
        "baslik": "Tedarikçi Değerlendirme (Tablo 7)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Tedarikci"],
        "aciklama": "Tedarikçi değerlendirme formu; sürdürülebilirlik kriterlerine göre skorlama maddeleri.",
    },
    {
        "id": "tablo8",
        "emoji": "✅",
        "baslik": "Onaylı Tedarikçi Listesi (Tablo 8)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Tablo 8"],
        "aciklama": "Onaylı tedarikçi listesi; kriterler ve onay tarihi sütunlarıyla doldurulmuş taslak.",
    },
    {
        "id": "tablo9",
        "emoji": "♻️",
        "baslik": "Tek Kullanımlık Plastik Sarfiyatı (Tablo 9)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Tablo 9"],
        "aciklama": "Plastik/ambalajlı ürün sarfiyat takip formatı; azaltma önerileriyle.",
    },
    {
        "id": "tablo10",
        "emoji": "🔌",
        "baslik": "Elektrik Tüketim Takibi (Tablo 10)",
        "tip": "deterministik",
        "cikti": ["Excel"],
        "kaynak": [],
        "aciklama": "Aylık elektrik tüketimi ve emisyon (kWh → kg CO₂e).",
    },
    {
        "id": "tablo11",
        "emoji": "🔥",
        "baslik": "Enerji / Yakıt Takibi (Tablo 11)",
        "tip": "deterministik",
        "cikti": ["Excel"],
        "kaynak": [],
        "aciklama": "Doğal gaz ve yakıt tüketimi; yenilenebilir oranı.",
    },
    {
        "id": "tablo12",
        "emoji": "🚿",
        "baslik": "Su Sarfiyatı Takibi (Tablo 12)",
        "tip": "deterministik",
        "cikti": ["Excel"],
        "kaynak": [],
        "aciklama": "Aylık su kullanımı; kişi ve oda-gün başına normalizasyon.",
    },
    {
        "id": "tablo13",
        "emoji": "🗑️",
        "baslik": "Atık Takibi (Tablo 13)",
        "tip": "deterministik",
        "cikti": ["Excel"],
        "kaynak": [],
        "aciklama": "Atık türü bazında aylık miktar; bertaraf ve geri kazanım.",
    },
    {
        "id": "politika_set",
        "emoji": "📋",
        "baslik": "Sürdürülebilirlik Politika Seti",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["POLITIKASI", "Politika"],
        "aciklama": "Çevre/atık, enerji, kadın & cinsiyet, çocuk hakları, satın alma ve ana politika belgesi; her biri kendi maddeleriyle tesise uyarlanır.",
    },
]


def sablon_bul(sablon_id: str) -> dict | None:
    for s in RAPOR_SABLONLARI:
        if s["id"] == sablon_id:
            return s
    return None


# ---------------- Deterministik (Tablo 10-13) ----------------
def _df_md(df) -> str:
    """DataFrame'i basit markdown tablosuna çevirir (tabulate bağımlılığı yok)."""
    import pandas as pd

    if df is None or len(df) == 0:
        return "(veri yok)"
    sutunlar = [str(c) for c in df.columns]
    satirlar = [[("" if pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False)]
    genislik = {i: max(len(s), *(len(r[i]) for r in satirlar)) for i, s in enumerate(sutunlar)}
    ayrac = "| " + " | ".join("-" * genislik[i] for i in range(len(sutunlar))) + " |"
    baslik = "| " + " | ".join(sutunlar[i].ljust(genislik[i]) for i in range(len(sutunlar))) + " |"
    govde = "\n".join(
        "| " + " | ".join(r[i].ljust(genislik[i]) for i in range(len(sutunlar))) + " |"
        for r in satirlar
    )
    return f"{baslik}\n{ayrac}\n{govde}"


def _deterministik_xlsx(sablon_id: str, sonuc: dict) -> bytes:
    tuketim = sonuc["tuketim"]
    if sablon_id == "tablo10":
        df = tablo10_elektrik(tuketim)
    elif sablon_id == "tablo11":
        df = tablo11_enerji(tuketim)
    elif sablon_id == "tablo12":
        tesis = sonuc["tesis"]
        df = tablo12_su(tuketim, tesis.get("dolu_oda_gun", 0), tesis.get("musteri", 0))
    elif sablon_id == "tablo13":
        df = tablo13_atik(tuketim)
    else:
        raise ValueError(f"Bilinmeyen deterministik şablon: {sablon_id}")
    import openpyxl  # noqa: F401

    buffer = BytesIO()
    with __import__("pandas").ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Tablo", index=False)
    return buffer.getvalue()


def _deterministik_md(sablon_id: str, sonuc: dict) -> str:
    tuketim = sonuc["tuketim"]
    if sablon_id == "tablo10":
        df = tablo10_elektrik(tuketim)
    elif sablon_id == "tablo11":
        df = tablo11_enerji(tuketim)
    elif sablon_id == "tablo12":
        tesis = sonuc["tesis"]
        df = tablo12_su(tuketim, tesis.get("dolu_oda_gun", 0), tesis.get("musteri", 0))
    elif sablon_id == "tablo13":
        df = tablo13_atik(tuketim)
    else:
        return ""
    return _df_md(df)


# ---------------- AI şablonları ----------------
def _ai_uretim(sablon: dict, tesis: dict, sonuc: dict | None, prefs: dict) -> str:
    import ai_engine

    return ai_engine.oner_rapor(sablon, tesis, sonuc, prefs)


# ---------------- Ana API ----------------
def rapor_uretim(sablon_id: str, tesis: dict, sonuc: dict | None, prefs: dict | None = None) -> dict:
    """Rapor üretir. Dönen: {"sablon_id", "tip", "metin", "xlsx": bytes|None}"""
    sablon = sablon_bul(sablon_id)
    if not sablon:
        raise ValueError(f"Bilinmeyen rapor şablonu: {sablon_id}")
    prefs = prefs or {}
    if sablon["tip"] == "deterministik":
        metin = _deterministik_md(sablon_id, sonuc or {})
        xlsx = _deterministik_xlsx(sablon_id, sonuc or {})
        return {"sablon_id": sablon_id, "tip": "deterministik", "metin": metin, "xlsx": xlsx}
    metin = _ai_uretim(sablon, tesis, sonuc, prefs)
    return {"sablon_id": sablon_id, "tip": "ai", "metin": metin, "xlsx": None}


# ---------------- Markdown tablo ayrıştırıcı (UI + DOCX + XLSX ortak) ----------------
def markdown_bloklar(metin: str) -> list[tuple]:
    """Markdown'ı bloklara böler: ("md", metin) veya ("tablo", DataFrame)."""
    satirlar = metin.splitlines()
    bloklar = []
    i = 0
    n = len(satirlar)
    while i < n:
        s = satirlar[i].strip()
        if s.startswith("|"):
            tab = []
            while i < n and satirlar[i].strip().startswith("|"):
                tab.append(satirlar[i].strip())
                i += 1
            rows = [[c.strip() for c in r.strip("|").split("|")] for r in tab]
            rows = [r for r in rows if not all(set(c) <= {"-", ":", " "} for c in r)]
            rows = [r for r in rows if any(r)]
            if len(rows) >= 2:
                cols = []
                gorulen = set()
                for j, c in enumerate(rows[0]):
                    ad = c.strip()
                    if not ad:
                        ad = f"Sütun {j + 1}"
                    if ad in gorulen:
                        ad = f"{ad} ({j + 1})"
                    gorulen.add(ad)
                    cols.append(ad)
                df = pd.DataFrame(rows[1:], columns=cols)
                bloklar.append(("tablo", df))
            elif rows:
                bloklar.append(("md", rows[0][0]))
        elif not s:
            i += 1
        else:
            parca = []
            while i < n:
                k = satirlar[i].strip()
                if not k or k.startswith("|"):
                    break
                parca.append(satirlar[i])
                i += 1
            bloklar.append(("md", "\n".join(parca)))
    return bloklar


# ---------------- DOCX (gerçek Word tabloları) ----------------
def _docx_ekle_blok(doc, blok):
    tur, icerik = blok
    if tur == "tablo":
        df = icerik
        if doc.tables:
            doc.add_paragraph()
        tablo = doc.add_table(rows=1, cols=max(1, len(df.columns)))
        tablo.style = "Light Grid Accent 1"
        for j, c in enumerate(df.columns):
            tablo.rows[0].cells[j].text = str(c)
        for _, row in df.iterrows():
            hucreler = tablo.add_row().cells
            for j, v in enumerate(row):
                if j < len(hucreler):
                    hucreler[j].text = "" if pd.isna(v) else str(v)
        return
    for satir in icerik.splitlines():
        s = satir.strip()
        if not s:
            continue
        if s.startswith("### "):
            doc.add_heading(s[4:].replace("**", ""), level=2)
        elif s.startswith("## "):
            doc.add_heading(s[3:].replace("**", ""), level=1)
        elif s.startswith("# "):
            doc.add_heading(s[2:].replace("**", ""), level=0)
        elif s.startswith(("-", "*")):
            doc.add_paragraph(s.lstrip("-* ").replace("**", ""), style="List Bullet")
        else:
            doc.add_paragraph(s.replace("**", ""))


def rapor_docx(metin: str) -> bytes:
    """Markdown'ı gerçek Word tablolarıyla .docx yapar."""
    from docx import Document

    doc = Document()
    for blok in markdown_bloklar(metin):
        _docx_ekle_blok(doc, blok)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ---------------- XLSX (tablo başına ayrı sayfa) ----------------
def rapor_xlsx(metin: str) -> bytes:
    """Markdown tablolarını ayrı sayfalara; kalan metni 'Metin' sayfasına yazar."""
    buffer = BytesIO()
    bloklar = markdown_bloklar(metin)
    tablolar = [b for b in bloklar if b[0] == "tablo"]
    metinler = [b[1] for b in bloklar if b[0] == "md"]
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for i, (_, df) in enumerate(tablolar):
            df.to_excel(writer, sheet_name=f"Tablo_{i + 1}"[:31], index=False)
        if metinler:
            metin_df = pd.DataFrame({"İçerik": [m for p in metinler for m in p.splitlines() if m.strip()]})
            metin_df.to_excel(writer, sheet_name="Metin", index=False)
        if not tablolar and not metinler:
            pd.DataFrame().to_excel(writer, sheet_name="Bos", index=False)
    return buffer.getvalue()


# ---------------- PDF (Türkçe font destekli) ----------------
_PDF_FONTLAR = None


def _pdf_font_ayar():
    """Türkçe karakterleri gösteren bir TTF font bulup reportlab'e kaydeder."""
    global _PDF_FONTLAR
    if _PDF_FONTLAR:
        return _PDF_FONTLAR
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    adaylar = [
        ("ArialTR", r"C:\Windows\Fonts\arial.ttf", "ArialTR-Bold", r"C:\Windows\Fonts\arialbd.ttf"),
        ("DejaVuSans", r"C:\Windows\Fonts\dejavusans.ttf", "DejaVuSans-Bold", r"C:\Windows\Fonts\dejavusans-bold.ttf"),
        ("TimesNewRomanTR", r"C:\Windows\Fonts\times.ttf", "TimesNewRomanTR-Bold", r"C:\Windows\Fonts\timesbd.ttf"),
    ]
    for ad, yol, bad, byol in adaylar:
        if os.path.exists(yol):
            pdfmetrics.registerFont(TTFont(ad, yol))
            if os.path.exists(byol):
                try:
                    pdfmetrics.registerFont(TTFont(bad, byol))
                except Exception:  # noqa: BLE001
                    bad = None
            _PDF_FONTLAR = (ad, bad)
            return _PDF_FONTLAR
    _PDF_FONTLAR = ("Helvetica", "Helvetica-Bold")
    return _PDF_FONTLAR


def rapor_pdf(metin: str) -> bytes:
    """Rapor metnini Türkçe karakter destekli PDF'e çevirir; tablolar gerçek PDF tablosu olur."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib import colors

    font_ad, font_bold = _pdf_font_ayar()
    bold = font_bold or font_ad
    buffer = BytesIO()
    stiller = getSampleStyleSheet()
    baslik = ParagraphStyle("Bas", parent=stiller["Title"], fontName=bold, fontSize=14, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=stiller["Heading2"], fontName=bold, fontSize=11.5, spaceBefore=6, spaceAfter=3)
    govde = ParagraphStyle("Govde", parent=stiller["BodyText"], fontName=font_ad, fontSize=9, leading=13)

    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=14 * mm, bottomMargin=14 * mm,
                            leftMargin=14 * mm, rightMargin=14 * mm)
    akis = []
    for tur, icerik in markdown_bloklar(metin):
        if tur == "tablo":
            df = icerik
            veri = [[str(c) for c in df.columns]] + [[("" if pd.isna(v) else str(v)) for v in r] for r in df.itertuples(index=False)]
            tablo = Table(veri, repeatRows=1, hAlign="LEFT")
            tablo.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), bold),
                ("FONTNAME", (0, 1), (-1, -1), font_ad),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d6b45")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd8cf")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4ee")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            akis.append(tablo)
            akis.append(Spacer(1, 6))
            continue
        for satir in icerik.splitlines():
            satir = satir.strip()
            if not satir:
                akis.append(Spacer(1, 4))
                continue
            if satir.startswith("### "):
                akis.append(Paragraph(satir[4:].replace("**", ""), h2))
            elif satir.startswith("# "):
                akis.append(Paragraph(satir[2:].replace("**", ""), baslik))
            elif satir.startswith(("-", "*")):
                akis.append(Paragraph("• " + satir.lstrip("-* ").replace("**", ""), govde))
            else:
                akis.append(Paragraph(satir.replace("**", ""), govde))
    doc.build(akis)
    return buffer.getvalue()
