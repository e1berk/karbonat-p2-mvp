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

from io import BytesIO

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
        "id": "anlati",
        "emoji": "📄",
        "baslik": "Sürdürülebilirlik Raporu (Tablo 4)",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["Raporlamasi", "Politika"],
        "aciklama": "TGA Tablo 4 formatında, tesis verileriyle doldurulmuş anlatı raporu; yönetim mesajı, performans, hedefler ve uyum maddeleri.",
    },
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
        "id": "politika_set",
        "emoji": "📋",
        "baslik": "Sürdürülebilirlik Politika Seti",
        "tip": "ai",
        "cikti": ["PDF"],
        "kaynak": ["POLITIKASI", "Politika"],
        "aciklama": "Çevre/atık, enerji, kadın & cinsiyet, çocuk hakları, satın alma ve ana politika belgesi; her biri kendi maddeleriyle tesise uyarlanır.",
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


def rapor_pdf(metin: str) -> bytes:
    """AI rapor metnini basit bir PDF'e çevirir."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = BytesIO()
    stiller = getSampleStyleSheet()
    baslik = ParagraphStyle("Bas", parent=stiller["Title"], fontName="Helvetica-Bold", fontSize=15, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=stiller["Heading2"], fontSize=12, spaceBefore=6, spaceAfter=3)
    govde = ParagraphStyle("Govde", parent=stiller["BodyText"], fontSize=9.5, leading=14)

    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm,
                            leftMargin=15 * mm, rightMargin=15 * mm)
    akis = []
    for satir in metin.splitlines():
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
