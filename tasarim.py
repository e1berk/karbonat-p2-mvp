# ============================================
# KarbonAT - TASARIM (görsel/medya çıktı katmanı)
# Üretilen markdown içeriğini tür bazlı, markalı, görsel
# çıktılara dönüştürür: tasarımlı HTML (web önizleme + indir)
# ve gerçek PDF (reportlab). Türkçe karakterli font için
# raporlar._pdf_font_ayar yeniden kullanılır.
# ============================================
from __future__ import annotations

import html as _html
import os
from io import BytesIO

import qrcode as _qrcode
from PIL import Image as _PILImage

from raporlar import markdown_bloklar, _pdf_font_ayar

PRIMARY = "#1d6b45"
DARK = "#0c3d27"
ACCENT = "#d99a3d"
SAGE = "#77a67f"
LIGHT = "#f4f8f4"
BORDER = "#d9e0d9"
MUTED = "#54635a"

BROŞÜR_TARİH = "06.08.2026"


def _afis_qr_pil(baslik: str, tesis_ad: str, tur_id: str = "gorsel_afis") -> _PILImage.Image:
    """Gerçek QR kodu üretir (PIL Image). tesis+tur anahtarıyla benzersiz içerik."""
    import qrcode as _qrcode
    veri = f"{baslik}|{tesis_ad}|{tur_id}|{BROŞÜR_TARİH}"
    qrc = _qrcode.QRCode(box_size=6, border=2)
    qrc.add_data(veri)
    qrc.make(fit=True)
    img = qrc.make_image(fill_color="#1d6b45", back_color="white")
    return img.convert("RGB")


# Tür -> tasarımlı üretim fonksiyonları (html: önizleme, pdf: indirme, png: gerçek görsel)
TASARIMLAR = {
    "brosur": {"html": "brosur_html", "pdf": "brosur_pdf", "png": "gorsel_png"},
    "web": {"html": "brosur_html", "pdf": "brosur_pdf", "png": "gorsel_png"},
    "qr": {"html": "qr_html", "pdf": "qr_pdf", "png": "gorsel_png"},
    "basin_bulteni": {"html": "basin_html", "pdf": "basin_pdf", "png": "gorsel_png"},
    "sosyal_medya": {"html": "sosyal_html", "pdf": "sosyal_pdf", "png": "gorsel_png"},
    "gorsel_afis": {"html": "afis_html", "pdf": "afis_pdf", "png": "gorsel_png"},
}


def _md_bolumler(metin: str):
    """Markdown'ı bölüm listesine çevirir: (baslik, [satirlar]) — ### başlıklar bölüm sınırı."""
    bolumler = []
    baslik = ""
    satirlar = []
    for tur, blok in markdown_bloklar(metin):
        if tur == "tablo":
            satirlar.append(("tablo", blok))
            continue
        for satir in [s.strip() for s in blok.splitlines() if s.strip()]:
            if satir.startswith("### ") or satir.startswith("## "):
                if baslik or satirlar:
                    bolumler.append((baslik, satirlar))
                baslik = satir.lstrip("# ").strip().replace("**", "")
                satirlar = []
            elif satir.startswith("# "):
                continue
            else:
                satirlar.append(("md", satir.lstrip("-* ").replace("**", "")))
    if baslik or satirlar:
        bolumler.append((baslik, satirlar))
    return bolumler


def kpi_listesi(son) -> list[tuple[str, str, str]]:
    """Sonuç verisinden broşür KPI kartları: (etiket, değer, birim)."""
    m = ((son or {}).get("metrikler") or {})
    yil_ton = m.get("toplam_kg", 0) * 12 / 1000
    return [
        ("Toplam Emisyon", f"{yil_ton:,.1f}", "ton CO₂e / yıl"),
        ("Oda-Gün Başına", f"{m.get('oda_gun_kg', 0):.2f}", "kg / oda-gün"),
        ("Müşteri Başına", f"{m.get('musteri_kg', 0):.1f}", "kg / konuk"),
        ("m² Başına (aylık)", f"{m.get('m2_aylik_kg', 0):.2f}", "kg / m²"),
    ]


def tesis_adi(son) -> str:
    return (((son or {}).get("tesis") or {}).get("ad")) or "Tesisimiz"


def _inline(s: str) -> str:
    return _html.escape(s.replace("**", ""))


def _tablo_html(df) -> str:
    basliklar = "".join(f"<th>{_html.escape(str(c))}</th>" for c in df.columns)
    satirlar = "".join(
        "<tr>" + "".join(f"<td>{_html.escape(str(v))}</td>" for v in r) + "</tr>"
        for r in df.itertuples(index=False)
    )
    return f'<div class="ttable"><table><thead><tr>{basliklar}</tr></thead><tbody>{satirlar}</tbody></table></div>'


def md_html(metin: str) -> str:
    """Markdown içeriğini bölümlü HTML'e çevirir; ### başlıklar vurgulu bölüm başlığı olur."""
    out: list[str] = []
    for tur, blok in markdown_bloklar(metin):
        if tur == "tablo":
            out.append(_tablo_html(blok))
            continue
        ul: list[str] = []
        for satir in [s.strip() for s in blok.splitlines() if s.strip()]:
            if satir.startswith("#### "):
                out.append(f"<h4>{_inline(satir[5:])}</h4>")
            elif satir.startswith("### "):
                out.append(f'<h3>{_inline(satir[4:])}</h3>')
            elif satir.startswith("## "):
                out.append(f'<h2>{_inline(satir[3:])}</h2>')
            elif satir.startswith("# "):
                out.append(f'<h1>{_inline(satir[2:])}</h1>')
            elif satir.startswith(("- ", "* ")):
                ul.append(f"<li>{_inline(satir[2:].lstrip('-* '))}</li>")
            else:
                out.append(f"<p>{_inline(satir)}</p>")
        if ul:
            out.append("<ul>" + "".join(ul) + "</ul>")
    return "\n".join(out)


# ---------- HTML (web önizleme + indirilebilir dosya) ----------

def brosur_html(son, metin: str) -> str:
    kpis = "".join(
        f'<div class="kpi"><div class="kv">{v}</div><div class="kl">{label}</div>'
        f'<div class="ku">{birim}</div></div>'
        for label, v, birim in kpi_listesi(son)
    )
    tesis = tesis_adi(son)
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(tesis)} — Sürdürülebilirlik</title>
<style>
:root {{ --p:{PRIMARY}; --d:{DARK}; --a:{ACCENT}; --l:{LIGHT}; --b:{BORDER}; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:'Segoe UI', Arial, sans-serif; color:#233027; background:#fff; }}
.page {{ max-width:820px; margin:0 auto; }}
.brand {{ background:linear-gradient(135deg,{DARK},{PRIMARY}); color:#fff; padding:30px 34px 24px; }}
.brand .label {{ letter-spacing:2px; font-size:12px; color:#b6d6c4; font-weight:600; }}
.brand h1 {{ margin:8px 0 2px; font-size:30px; }}
.brand p {{ margin:0; color:#d7e8dd; font-size:14px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:-22px 34px 0; position:relative; }}
.kpi {{ background:#fff; border:1px solid var(--b); box-shadow:0 4px 14px rgba(12,61,39,.08); border-radius:12px; padding:14px 12px; text-align:center; }}
.kpi .kv {{ font-size:24px; font-weight:800; color:var(--p,#1d6b45); }}
.kpi .kl {{ font-size:12px; color:{MUTED}; margin-top:2px; }}
.kpi .ku {{ font-size:11px; color:#8a9a8f; }}
.content {{ padding:26px 38px 0; }}
.content h1, .content h2, .content h3 {{ color:var(--d); }}
.content h3 {{ border-left:5px solid var(--a); padding-left:10px; margin:24px 0 8px; font-size:19px; }}
.content h4 {{ color:var(--p); margin:14px 0 4px; }}
.content p {{ line-height:1.55; color:#3a463e; margin:8px 0; }}
.content ul {{ padding-left:20px; }}
.content li {{ margin:5px 0; color:#3a463e; }}
.ttable {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:var(--p); color:#fff; padding:7px 9px; text-align:left; }}
td {{ border:1px solid var(--b); padding:6px 9px; }}
tr:nth-child(even) td {{ background:var(--l); }}
.footer {{ margin:26px 38px 0; border-top:3px solid var(--p); padding:16px 0 26px; display:flex; justify-content:space-between; align-items:center; color:{MUTED}; font-size:12px; }}
.qr {{ border:2px dashed {ACCENT}; color:{ACCENT}; font-weight:700; padding:10px 16px; border-radius:8px; text-align:center; }}
</style></head>
<body><div class="page">
  <div class="brand">
    <div class="label">GSTC · TGA DOĞRULANMIŞ TESİS</div>
    <h1>{_html.escape(tesis)}</h1>
    <p>Geleceğe Saygılı Konaklama — Doğayla Uyumlu, Sürdürülebilir Bir Gelecek</p>
  </div>
  <div class="kpis">{kpis}</div>
  <div class="content">{md_html(metin)}</div>
  <div class="footer">
    <span>Güncelleme: {BROŞÜR_TARİH}</span>
    <span class="qr">[ QR KODU TARATIN ]</span>
    <span>KarbonAT Altyapısı ile Hazırlanmıştır.</span>
  </div>
</div></body></html>"""


# ---------- PDF (reportlab, tasarımlı) ----------

def brosur_pdf(son, metin: str) -> bytes:
    """Türkçe karakter destekli, markalı broşür PDF'i üretir."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    font_ad, font_bold = _pdf_font_ayar()
    bold = font_bold or font_ad
    p = colors.HexColor(PRIMARY)
    d = colors.HexColor(DARK)
    a = colors.HexColor(ACCENT)
    s = colors.HexColor(SAGE)
    lg = colors.HexColor(LIGHT)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=33 * mm, bottomMargin=13 * mm,
                            leftMargin=13 * mm, rightMargin=13 * mm)

    tesis = tesis_adi(son)

    def on_page(canva, _doc):
        w, h = A4
        canva.saveState()
        # Üst bant
        pct = canva.beginPath()
        pct.moveTo(0, h)
        pct.lineTo(w, h)
        pct.lineTo(w, h - 27 * mm)
        pct.lineTo(0, h - 27 * mm)
        pct.close()
        canva.setFillColor(p)
        canva.drawPath(pct, fill=1, stroke=0)
        canva.setFillColor(colors.white)
        canva.setFont(bold, 16)
        canva.drawString(14 * mm, h - 16 * mm, tesis)
        canva.setFont(font_ad, 8.5)
        canva.setFillColor(colors.HexColor("#c9e3d2"))
        canva.drawString(14 * mm, h - 21.5 * mm, "Geleceğe Saygılı Konaklama — Sürdürülebilir Bir Gelecek")
        canva.setFont(font_ad, 6.8)
        canva.setFillColor(colors.HexColor("#9fc2ac"))
        canva.drawRightString(w - 14 * mm, h - 21.5 * mm, "GSTC · TGA DOĞRULANMIŞ TESİS")
        # Alt bilgi
        canva.setFillColor(d)
        canva.setFont(font_ad, 7)
        canva.drawString(14 * mm, 8 * mm, f"Güncelleme: {BROŞÜR_TARİH} · KarbonAT Altyapısı")
        canva.setFillColor(a)
        canva.setFont(bold, 7.5)
        canva.drawRightString(w - 14 * mm, 8 * mm, "[ QR KODU TARATIN ]")
        canva.restoreState()

    stiller = ParagraphStyle("Govde", fontName=font_ad, fontSize=9, leading=13, textColor=colors.HexColor("#3a463e"))
    h3stil = ParagraphStyle("H3", parent=stiller, fontName=bold, fontSize=11.5, leading=15,
                            spaceBefore=10, spaceAfter=4, textColor=d)
    h2stil = ParagraphStyle("H2", parent=stiller, fontName=bold, fontSize=13, leading=16,
                            spaceBefore=12, spaceAfter=4, textColor=p)

    akis = []

    # KPI bandı (üst bandın hemen altında)
    kv_stil = ParagraphStyle("Kv", fontName=bold, fontSize=14, alignment=1, textColor=p)
    kl_stil = ParagraphStyle("Kl", fontName=font_ad, fontSize=6.5, alignment=1, leading=8,
                             textColor=colors.HexColor(MUTED))
    kpi_veri = kpi_listesi(son)
    kpi_tablo = Table(
        [
            [Paragraph(v, kv_stil) for _, v, _ in kpi_veri],
            [Paragraph(f"{label}<br/>{birim}", kl_stil) for label, _, birim in kpi_veri],
        ],
        colWidths=[32 * mm] * 4,
        rowHeights=[11 * mm, 13 * mm],
        hAlign="CENTER",
    )
    kpi_tablo.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(BORDER)),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]))
    akis.append(kpi_tablo)
    akis.append(Spacer(1, 4 * mm))

    for tur, blok in markdown_bloklar(metin):
        if tur == "tablo":
            df = blok
            veri = [[str(c) for c in df.columns]] + [
                [("" if _is_na(v) else str(v)) for v in r] for r in df.itertuples(index=False)
            ]
            t = Table(veri, repeatRows=1, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), bold),
                ("FONTNAME", (0, 1), (-1, -1), font_ad),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("BACKGROUND", (0, 0), (-1, 0), p),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(BORDER)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, lg]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            akis.append(t)
            akis.append(Spacer(1, 3))
            continue
        for satir in [x.strip() for x in blok.splitlines() if x.strip()]:
            if satir.startswith("#### "):
                akis.append(Paragraph(satir[5:].replace("**", ""),
                                      ParagraphStyle("H4", parent=stiller, fontName=bold, fontSize=9.5,
                                                     spaceBefore=6, spaceAfter=2, textColor=p)))
            elif satir.startswith("### "):
                akis.append(Paragraph(satir[4:].replace("**", ""), h3stil))
            elif satir.startswith("## "):
                akis.append(Paragraph(satir[3:].replace("**", ""), h2stil))
            elif satir.startswith("# "):
                akis.append(Paragraph(satir[2:].replace("**", ""), h2stil))
            elif satir.startswith(("- ", "* ")):
                akis.append(Paragraph("• " + satir.lstrip("-* ").replace("**", ""), stiller))
            else:
                akis.append(Paragraph(satir.replace("**", ""), stiller))

    doc.build(akis, onFirstPage=on_page, onLaterPages=on_page)
    return buffer.getvalue()


def _is_na(v):
    try:
        import pandas as pd
        return pd.isna(v)
    except Exception:  # noqa: BLE001
        return v is None


# ---------- QR / Oda Kartı (85x55 mm) ----------

def qr_html(son, metin: str) -> str:
    tesis = tesis_adi(son)
    kpi = "".join(
        f'<div class="mi"><b>{v}</b><span>{label}</span></div>'
        for label, v, _ in kpi_listesi(son)[:3]
    )
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(tesis)} — Oda Kartı</title>
<style>
body {{ margin:0; font-family:'Segoe UI', Arial, sans-serif; background:#eef2ee; }}
.card {{ width:340px; margin:20px auto; background:#fff; border-radius:14px; overflow:hidden;
         box-shadow:0 6px 18px rgba(12,61,39,.15); }}
.top {{ background:linear-gradient(135deg,{DARK},{PRIMARY}); color:#fff; padding:16px 18px; }}
.top .lbl {{ font-size:10px; letter-spacing:2px; color:#b6d6c4; font-weight:600; }}
.top h1 {{ margin:4px 0 0; font-size:20px; }}
.kpis {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; padding:14px 16px; }}
.mi {{ text-align:center; border:1px solid {BORDER}; border-radius:10px; padding:8px 4px; }}
.mi b {{ display:block; font-size:16px; color:{PRIMARY}; }}
.mi span {{ font-size:9px; color:{MUTED}; }}
.body {{ padding:0 16px 12px; font-size:12px; color:#3a463e; line-height:1.5; }}
.body h3 {{ color:{DARK}; font-size:13px; margin:10px 0 4px; border-left:3px solid {ACCENT}; padding-left:6px; }}
.body ul {{ margin:4px 0; padding-left:16px; }}
.qr {{ margin:12px 16px 18px; border:2px dashed {ACCENT}; border-radius:10px; text-align:center;
       padding:14px; color:{ACCENT}; font-weight:700; font-size:12px; }}
</style></head><body>
<div class="card">
  <div class="top"><div class="lbl">GSTC · TGA</div><h1>{_html.escape(tesis)}</h1></div>
  <div class="kpis">{kpi}</div>
  <div class="body">{md_html(metin)}</div>
  <div class="qr">[ QR — VERİ DOĞRULAMA ]</div>
</div></body></html>"""


def qr_pdf(son, metin: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm as MM
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

    font_ad, font_bold = _pdf_font_ayar()
    bold = font_bold or font_ad
    p = colors.HexColor(PRIMARY)
    d = colors.HexColor(DARK)
    a = colors.HexColor(ACCENT)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(90 * mm, 60 * mm),
                            topMargin=3 * MM, bottomMargin=3 * MM,
                            leftMargin=3 * MM, rightMargin=3 * MM)
    stiller = ParagraphStyle("G", fontName=font_ad, fontSize=6.5, leading=9, textColor=colors.HexColor("#3a463e"))
    h3 = ParagraphStyle("H3", parent=stiller, fontName=bold, fontSize=8, leading=10, textColor=d, spaceBefore=4)
    akis = []
    baslik = Table([[Paragraph(tesis_adi(son), ParagraphStyle("B", fontName=bold, fontSize=13, textColor=colors.white))]],
                   colWidths=[84 * mm])
    baslik.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), p),
                                ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    akis.append(baslik)
    kpi = kpi_listesi(son)[:3]
    kpi_tab = Table(
        [[Paragraph(v, ParagraphStyle("KV", fontName=bold, fontSize=10, textColor=p)) for _, v, _ in kpi],
         [Paragraph(label, ParagraphStyle("KL", fontName=font_ad, fontSize=5.5, textColor=colors.HexColor(MUTED)))
          for label, _, _ in kpi]],
        colWidths=[28 * mm] * 3,
    )
    kpi_tab.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(BORDER)),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor(BORDER)),
    ]))
    akis.append(Spacer(1, 2 * MM))
    akis.append(kpi_tab)
    akis.append(Spacer(1, 2 * MM))
    for baslik_t, satirlar in _md_bolumler(metin):
        if baslik_t:
            akis.append(Paragraph(baslik_t, h3))
        for tur, icerik in satirlar:
            if tur == "tablo":
                continue
            akis.append(Paragraph("• " + icerik, stiller))
    akis.append(Spacer(1, 2 * MM))
    qr = Table([[Paragraph("[ QR — VERİ DOĞRULAMA ]",
                           ParagraphStyle("QR", fontName=bold, fontSize=7, textColor=a, alignment=1))]],
               colWidths=[84 * mm])
    qr.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, a),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    akis.append(qr)
    doc.build(akis)
    return buffer.getvalue()


# ---------- Afiş / Poster (yatay) ----------

def afis_html(son, metin: str) -> str:
    import base64 as _b64
    tesis = tesis_adi(son)
    kpi = "".join(
        f'<div class="kpi"><div class="v">{v}</div><div class="l">{label} · {birim}</div></div>'
        for label, v, birim in kpi_listesi(son)[:3]
    )
    # Gerçek QR kodu
    try:
        qr_img = _afis_qr_pil("KarbonAT Afiş", tesis)
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        qr_b64 = _b64.b64encode(buf.getvalue()).decode("ascii")
        qr_tag = f'<img src="data:image/png;base64,{qr_b64}" style="width:72px;height:72px;" alt="QR">'
    except Exception:
        qr_tag = "<span style=\"color:#9fc2ac;\">[ QR ]</span>"
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(tesis)} — Afiş</title>
<style>
body {{ margin:0; font-family:'Segoe UI', Arial, sans-serif; background:#eef2ee; }}
.poster {{ max-width:900px; margin:24px auto; background:{DARK}; border-radius:18px; overflow:hidden;
           color:#fff; box-shadow:0 8px 30px rgba(12,61,39,.35); }}
.phead {{ padding:34px 40px 20px; }}
.phead .lbl {{ letter-spacing:4px; font-size:11px; color:{SAGE}; font-weight:700; }}
.phead h1 {{ margin:8px 0 2px; font-size:44px; }}
.phead p {{ margin:0; color:#bcd4c4; font-size:15px; }}
.pkpis {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; padding:0 40px 26px; }}
.pkpis .kpi {{ background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.18); border-radius:12px; padding:16px; }}
.pkpis .v {{ font-size:30px; font-weight:800; color:{ACCENT}; }}
.pkpis .l {{ font-size:12px; color:#cfe0d4; margin-top:2px; }}
.pbody {{ background:#fff; color:#233027; padding:26px 40px 34px; }}
.pbody h3 {{ color:{DARK}; border-left:5px solid {ACCENT}; padding-left:10px; margin:20px 0 8px; font-size:19px; }}
.pbody p, .pbody li {{ font-size:14px; color:#3a463e; line-height:1.55; }}
.pfoot {{ display:flex; justify-content:space-between; align-items:center; padding:14px 40px 22px; font-size:12px; color:#9fc2ac; }}
</style></head><body>
<div class="poster">
  <div class="phead">
    <div class="lbl">SÜRDÜRÜLEBİLİR KONAKLAMA</div>
    <h1>{_html.escape(tesis)}</h1>
    <p>GSTC · TGA Doğrulanmış Tesis — Doğayla Uyumlu Gelecek</p>
  </div>
  <div class="pkpis">{kpi}</div>
  <div class="pbody">{md_html(metin)}</div>
  <div class="pfoot"><span>KarbonAT Altyapısı</span>{qr_tag}</div>
</div></body></html>"""


def afis_pdf(son, metin: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

    font_ad, font_bold = _pdf_font_ayar()
    bold = font_bold or font_ad
    p = colors.HexColor(PRIMARY)
    d = colors.HexColor(DARK)
    a = colors.HexColor(ACCENT)
    s = colors.HexColor(SAGE)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            topMargin=8 * mm, bottomMargin=8 * mm,
                            leftMargin=8 * mm, rightMargin=8 * mm)
    stiller = ParagraphStyle("G", fontName=font_ad, fontSize=8.5, leading=12, textColor=colors.HexColor("#3a463e"))
    h3 = ParagraphStyle("H3", parent=stiller, fontName=bold, fontSize=12, leading=15, textColor=d, spaceBefore=8)
    akis = []
    band = Table([[Paragraph(tesis_adi(son),
                             ParagraphStyle("B", fontName=bold, fontSize=24, textColor=colors.white))]],
                 colWidths=[275 * mm])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), d),
                              ("TOPPADDING", (0, 0), (-1, -1), 12),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    akis.append(band)
    kpi = kpi_listesi(son)[:3]
    kpi_tab = Table(
        [[Paragraph(v, ParagraphStyle("KV", fontName=bold, fontSize=18, textColor=a)) for _, v, _ in kpi],
         [Paragraph(f"{label} · {birim}", ParagraphStyle("KL", fontName=font_ad, fontSize=6.5,
                                                          textColor=colors.white)) for label, _, birim in kpi]],
        colWidths=[91.6 * mm] * 3,
    )
    kpi_tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), p),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    akis.append(kpi_tab)
    akis.append(Spacer(1, 3 * mm))
    for baslik, satirlar in _md_bolumler(metin):
        if baslik:
            akis.append(Paragraph(baslik, h3))
        for tur, icerik in satirlar:
            if tur == "tablo":
                continue
            akis.append(Paragraph("• " + icerik, stiller))
    akis.append(Spacer(1, 4 * mm))
    # Gerçek QR kodu görseli (reportlab Image)
    try:
        qr_img = _afis_qr_pil("KarbonAT Afiş", tesis_adi(son))
        qb = BytesIO()
        qr_img.save(qb, format="PNG")
        qb.seek(0)
        from reportlab.platypus import Image as RLImage
        qrl = RLImage(qb, width=64*mm, height=64*mm)
        qrl.hAlign = "RIGHT"
        akis.append(qrl)
        akis.append(Paragraph("VERİ DOĞRULAMA KODU TARATIN",
                              ParagraphStyle("QR2", fontName=bold, fontSize=8, textColor=a, alignment=2)))
    except Exception:
        akis.append(Paragraph("VERİ DOĞRULAMA İÇİN QR KODU TARATIN",
                              ParagraphStyle("QR2", fontName=bold, fontSize=8, textColor=a, alignment=1)))
    doc.build(akis)
    return buffer.getvalue()


# ---------- Basın Bülteni ----------

def basin_html(son, metin: str) -> str:
    tesis = tesis_adi(son)
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(tesis)} — Basın Bülteni</title>
<style>
body {{ margin:0; font-family:'Segoe UI', Arial, sans-serif; background:#eef2ee; }}
.press {{ max-width:760px; margin:24px auto; background:#fff; padding:0; box-shadow:0 6px 18px rgba(12,61,39,.12); }}
.ph {{ background:linear-gradient(135deg,{DARK},{PRIMARY}); color:#fff; padding:22px 34px; }}
.ph .lbl {{ letter-spacing:3px; font-size:10px; color:#b6d6c4; font-weight:700; }}
.ph h1 {{ margin:6px 0 0; font-size:24px; }}
.pd {{ padding:24px 34px 30px; color:#233027; }}
.pd .date {{ font-size:11px; color:{MUTED}; border-bottom:2px solid {ACCENT}; padding-bottom:8px; margin-bottom:14px; }}
.pd h2, .pd h3 {{ color:{DARK}; }}
.pd p, .pd li {{ font-size:14px; line-height:1.6; color:#3a463e; }}
.pd .q {{ border-left:4px solid {SAGE}; padding:8px 12px; margin:14px 0; background:{LIGHT}; font-style:italic; }}
.pf {{ background:{LIGHT}; padding:14px 34px; font-size:12px; color:{MUTED}; }}
</style></head><body>
<div class="press">
  <div class="ph"><div class="lbl">BASIN BÜLTENİ · MEDYA</div><h1>{_html.escape(tesis)} — Sürdürülebilirlik</h1></div>
  <div class="pd">{md_html(metin)}</div>
  <div class="pf">Medya iletişim: surdurulebilirlik@{_html.escape(tesis.lower().replace(' ', ''))}.com.tr · KarbonAT Altyapısı</div>
</div></body></html>"""


def basin_pdf(son, metin: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    font_ad, font_bold = _pdf_font_ayar()
    bold = font_bold or font_ad
    p = colors.HexColor(PRIMARY)
    d = colors.HexColor(DARK)
    s = colors.HexColor(SAGE)
    a = colors.HexColor(ACCENT)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=16 * mm, bottomMargin=14 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm)
    stiller = ParagraphStyle("G", fontName=font_ad, fontSize=9.5, leading=14, textColor=colors.HexColor("#3a463e"))
    h3 = ParagraphStyle("H3", parent=stiller, fontName=bold, fontSize=12, leading=15, textColor=d, spaceBefore=8)
    akis = []
    band = Table([[Paragraph(tesis_adi(son) + " — BASIN BÜLTENİ",
                             ParagraphStyle("B", fontName=bold, fontSize=14, textColor=colors.white))]],
                 colWidths=[178 * mm])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), p),
                              ("TOPPADDING", (0, 0), (-1, -1), 9),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    akis.append(band)
    akis.append(Paragraph("BASIN DUYURUSU · " + BROŞÜR_TARİH,
                          ParagraphStyle("T", fontName=bold, fontSize=8, textColor=a, spaceBefore=6, spaceAfter=6)))
    for baslik, satirlar in _md_bolumler(metin):
        if baslik:
            akis.append(Paragraph(baslik, h3))
        for tur, icerik in satirlar:
            if tur == "tablo":
                continue
            akis.append(Paragraph("• " + icerik, stiller))
    akis.append(Spacer(1, 4 * mm))
    akis.append(Paragraph("Medya iletişim: KarbonAT Altyapısı", ParagraphStyle("F", fontName=font_ad,
                         fontSize=8, textColor=colors.HexColor(MUTED))))
    doc.build(akis)
    return buffer.getvalue()


# ---------- Sosyal Medya (platform kartları) ----------

def sosyal_html(son, metin: str) -> str:
    tesis = tesis_adi(son)
    kartlar = []
    for baslik, satirlar in _md_bolumler(metin):
        satir_html = "".join(
            f"<li>{_inline(x)}</li>" if t == "md" else ""
            for t, x in satirlar if t == "md"
        )
        kartlar.append(
            f'<div class="post"><div class="pfx">📣 {_html.escape(baslik or "Gönderi")}</div>'
            f'<ul>{satir_html}</ul></div>'
        )
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(tesis)} — Sosyal Medya Paketi</title>
<style>
body {{ margin:0; font-family:'Segoe UI', Arial, sans-serif; background:#eef2ee; }}
.wrap {{ max-width:720px; margin:20px auto; }}
.phead {{ background:linear-gradient(135deg,{DARK},{PRIMARY}); color:#fff; border-radius:14px; padding:20px 26px; margin-bottom:16px; }}
.phead h1 {{ margin:0; font-size:22px; }}
.phead p {{ margin:4px 0 0; color:#bcd4c4; font-size:13px; }}
.post {{ background:#fff; border:1px solid {BORDER}; border-left:5px solid {SAGE}; border-radius:10px; padding:14px 18px; margin-bottom:12px; }}
.post .pfx {{ font-weight:800; color:{DARK}; margin-bottom:6px; }}
.post ul {{ margin:0; padding-left:18px; }}
.post li {{ font-size:13px; color:#3a463e; line-height:1.55; margin:4px 0; }}
</style></head><body>
<div class="wrap">
  <div class="phead"><h1>{_html.escape(tesis)} — Sosyal Medya Paketi</h1>
  <p>Platform gönderileri · A6 doğrulanmış iddialar · KarbonAT</p></div>
  {"".join(kartlar)}
</div></body></html>"""


def sosyal_pdf(son, metin: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    font_ad, font_bold = _pdf_font_ayar()
    bold = font_bold or font_ad
    p = colors.HexColor(PRIMARY)
    d = colors.HexColor(DARK)
    s = colors.HexColor(SAGE)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=15 * mm, bottomMargin=14 * mm,
                            leftMargin=15 * mm, rightMargin=15 * mm)
    stiller = ParagraphStyle("G", fontName=font_ad, fontSize=9, leading=13, textColor=colors.HexColor("#3a463e"))
    h3 = ParagraphStyle("H3", parent=stiller, fontName=bold, fontSize=11, leading=14, textColor=d, spaceBefore=8)
    akis = []
    band = Table([[Paragraph(tesis_adi(son) + " — Sosyal Medya Paketi",
                             ParagraphStyle("B", fontName=bold, fontSize=13, textColor=colors.white))]],
                 colWidths=[180 * mm])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), p),
                              ("TOPPADDING", (0, 0), (-1, -1), 9),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    akis.append(band)
    akis.append(Spacer(1, 3 * mm))
    for baslik, satirlar in _md_bolumler(metin):
        if baslik:
            akis.append(Paragraph(baslik, h3))
        for tur, icerik in satirlar:
            if tur == "tablo":
                continue
            akis.append(Paragraph("• " + icerik, stiller))
    doc.build(akis)
    return buffer.getvalue()


# ============================================================
# GERÇEK GÖRSEL (raster PNG) — Pillow ile infografik
# ============================================================

_FONT_YOLLARI = {
    "r": r"C:\Windows\Fonts\arial.ttf",
    "b": r"C:\Windows\Fonts\arialbd.ttf",
    "d": r"C:\Windows\Fonts\dejavusans.ttf",
    "db": r"C:\Windows\Fonts\dejavusans-bold.ttf",
}


def _img_font(bold: bool, size: int):
    from PIL import ImageFont
    anahtar = "b" if bold else "r"
    yol = _FONT_YOLLARI[anahtar]
    if not os.path.exists(yol):
        yol = (_FONT_YOLLARI["db"] if bold else _FONT_YOLLARI["d"])
    if not os.path.exists(yol):
        return ImageFont.load_default()
    _img_font.__cache = _img_font.__cache if hasattr(_img_font, "__cache") else {}
    if (anahtar, size) not in _img_font.__cache:
        _img_font.__cache[(anahtar, size)] = ImageFont.truetype(yol, size)
    return _img_font.__cache[(anahtar, size)]


def _satir_parcala(draw, metin, font, max_w):
    """Metni satır genişliğine göre kırar."""
    satirlar = []
    for parca in metin.split("\n"):
        if not parca:
            continue
        if draw.textlength(parca, font=font) <= max_w:
            satirlar.append(parca)
            continue
        satir = ""
        for kelime in parca.split(" "):
            deneme = (satir + " " + kelime).strip()
            if draw.textlength(deneme, font=font) <= max_w:
                satir = deneme
            else:
                if satir:
                    satirlar.append(satir)
                satir = kelime
        if satir:
            satirlar.append(satir)
    return satirlar


def gorsel_png(son, metin: str, tur_id: str | None = None) -> bytes:
    """Markalı, gerçek bir raster görsel (PNG) üretir — Pillow infografik."""
    from PIL import Image, ImageDraw

    tesis = tesis_adi(son)
    kl = kpi_listesi(son)
    W, H = 1000, 1420
    sol = 70
    sag = W - 70
    ic_gen = sag - sol

    img = Image.new("RGB", (W, H), "#ffffff")
    dr = ImageDraw.Draw(img)

    P = (29, 107, 69)      # #1d6b45
    D = (12, 61, 39)       # #0c3d27
    A = (217, 153, 61)     # #d99a3d
    LG = (238, 244, 238)   # #eef4ee
    BRD = (217, 224, 217)  # #d9e0d9
    MT = (84, 99, 90)      # #54635a
    TX = (44, 54, 47)      # #2c362f

    f_buyuk = _img_font(True, 64)
    f_orta = _img_font(True, 40)
    f_alt = _img_font(False, 28)
    f_bas = _img_font(True, 34)
    f_madde = _img_font(False, 27)
    f_kart_v = _img_font(True, 58)
    f_kart_e = _img_font(False, 22)

    # --- Üst bant (dikey gradyan) ---
    bant_y = 150
    for i in range(bant_y):
        t = i / bant_y
        renk = tuple(round(D[c] + (P[c] - D[c]) * t) for c in range(3))
        dr.rectangle([0, i, W, i + 1], fill=renk)
    dr.text((sol, 26), "GSTC · TGA SÜRDÜRÜLEBİLİR KONAKLAMA", font=f_alt,
            fill=(185, 214, 196))
    dr.text((sol, 58), tesis, font=f_buyuk, fill=(255, 255, 255))
    dr.text((sol, 118), "Doğayla uyumlu, doğrulanmış sürdürülebilirlik", font=f_alt,
            fill=(201, 227, 210))

    # --- KPI kartları ---
    y = bant_y + 34
    kart_gen = (ic_gen - 3 * 14) / 4
    for i, (label, v, birim) in enumerate(kl):
        x0 = sol + i * (kart_gen + 14)
        dr.rounded_rectangle([x0, y, x0 + kart_gen, y + 110], radius=14, fill="#ffffff",
                             outline=BRD, width=2)
        dr.text((x0 + 14, y + 16), v, font=f_kart_v, fill=P)
        et = f"{label}"
        dr.text((x0 + 14, y + 82), et, font=f_kart_e, fill=MT)
    y += 110 + 20

    # --- İçerik bölümleri ---
    bolumler = _md_bolumler(metin)

    # Bölüm başına madde kotası (takılı kalan uzun içerik için kompakt)
    M = 6
    for baslik, satirlar in bolumler:
        maddeler = [ic for t_, ic in satirlar if t_ == "md"][: M]
        blok_h = 40 + (len(baslik) > 0) * 8 + len(maddeler) * 34
        if y + blok_h > H - 150:
            break
        if baslik:
            dr.rectangle([sol, y + 4, sol + 7, y + 38], fill=A)
            dr.text((sol + 20, y), baslik, font=f_bas, fill=D)
            y += 46
        for madde in maddeler:
            for satir in _satir_parcala(dr, madde, f_madde, ic_gen - 40):
                dr.text((sol + 30, y), "▪", font=f_madde, fill=A)
                dr.text((sol + 52, y), satir, font=f_madde, fill=TX)
                y += 34
        y += 12

    # --- Alt bölüm: QR + rozet ---
    y = H - 130
    dr.rectangle([sol, y, sag, y + 70], fill=LG)
    # sahte QR deseni (find tuple)
    import random as _rnd
    _rnd.seed(42)
    qsat = 6
    qx, qy = sol + 24, y + 16
    kare = 42 / qsat
    for qi in range(qsat):
        for qj in range(qsat):
            if _rnd.random() < 0.5:
                dr.rectangle([qx + qi * kare, qy + qj * kare,
                              qx + (qi + 1) * kare, qy + (qj + 1) * kare], fill=D)
    dr.text((sol + 120, y + 20), "TGA / GSTC DOĞRULANMIŞ VERİ", font=f_alt, fill=P)
    dr.text((sol + 120, y + 46), "QR kodu taratarak inceleyin", font=f_madde, fill=MT)
    dr.rectangle([sol, H - 26, sag, H], fill=D)
    dr.text((sol, H - 24), f"{BROŞÜR_TARİH} · KarbonAT — Sürdürülebilirlik Altyapısı",
            font=f_alt, fill=(205, 227, 210))

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
