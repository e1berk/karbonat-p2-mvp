# ============================================
# KarbonAT - TGA Takip Tabloları Üretici
# Tablo 10 (Elektrik) / 11 (Enerji) / 12 (Su) / 13 (Atık) + Kimyasal Envanter
# ============================================

import pandas as pd

from factors import EMISSION_FACTORS

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

ELEKTRIK_KATEGORI = "Elektrik"
SU_KATEGORI = "Su"
ATIK_KATEGORI = "Atık Yönetimi"
KIMYASAL_KATEGORI = "Kimyasal Tüketimi"

YENILENEBILIR_ELEKTRIK = {
    "Şebeke (yenilenebilir YEK-G sertifikalı)",
    "Güneş Enerjisi (PV)",
    "Rüzgar Enerjisi",
}

# Atık türü -> bertaraf yöntemi (geri dönüşüm değerlendirmesi için)
ATIK_BERTARAF = {
    "Cam (kg)": "Geri dönüşüm",
    "Kağıt (kg)": "Geri dönüşüm",
    "Metal (kg)": "Geri dönüşüm",
    "Organik Atık (kg)": "Kompost / biyolojik",
    "Plastik Atık (kg)": "Enerji geri kazanımı",
}


def format_donem(period):
    """'2026-07' -> 'Temmuz 2026'"""
    try:
        yil, ay = str(period).split("-")
        return f"{AYLAR[int(ay) - 1]} {yil}"
    except Exception:
        return str(period)


def _aktif(tuketim, kategori):
    return {
        k: v for k, v in tuketim.get(kategori, {}).items()
        if v and v > 0
    }


def tablo10_elektrik(tuketim):
    """Elektrik Tüketim Takip Tablosu (kWh, emisyon)."""
    rows = []
    for alt_tur, miktar in _aktif(tuketim, ELEKTRIK_KATEGORI).items():
        faktor = EMISSION_FACTORS[ELEKTRIK_KATEGORI].get(alt_tur, 0.0)
        rows.append({
            "Alt Tür": alt_tur,
            "Tüketim (kWh)": miktar,
            "Emisyon Faktörü (kgCO₂e/kWh)": faktor,
            "Emisyon (kgCO₂e)": round(miktar * faktor, 2),
        })
    if rows:
        toplam_kwh = sum(r["Tüketim (kWh)"] for r in rows)
        toplam_co2 = sum(r["Emisyon (kgCO₂e)"] for r in rows)
        rows.append({
            "Alt Tür": "TOPLAM",
            "Tüketim (kWh)": toplam_kwh,
            "Emisyon Faktörü (kgCO₂e/kWh)": "",
            "Emisyon (kgCO₂e)": round(toplam_co2, 2),
        })
    return pd.DataFrame(rows)


def tablo11_enerji(tuketim):
    """Enerji Tablosu — yenilenebilir oranı (elektrik + doğal gaz + yakıtlar + araç filosu)."""
    from factors import EMISSION_FACTORS, SCOPE_ATAMASI
    rows = []
    yenilenebilir_kwh = 0.0
    # Elektrik
    for alt_tur, miktar in _aktif(tuketim, "Elektrik").items():
        is_yenilenebilir = alt_tur in YENILENEBILIR_ELEKTRIK
        if is_yenilenebilir:
            yenilenebilir_kwh += miktar
        rows.append({
            "Enerji Kaynağı": alt_tur,
            "Kategori": "Elektrik",
            "Birim": "kWh",
            "Tüketim": miktar,
            "Yenilenebilir": "Evet" if is_yenilenebilir else "Hayır",
        })
    # Doğal Gaz ve Yakıtlar
    for alt_tur, miktar in _aktif(tuketim, "Doğal Gaz ve Yakıtlar").items():
        rows.append({
            "Enerji Kaynağı": alt_tur,
            "Kategori": "Doğal Gaz ve Yakıtlar",
            "Birim": "m³ / kg",
            "Tüketim": miktar,
            "Yenilenebilir": "Hayır",
        })
    # Soğutucu & F-Gaz
    for alt_tur, miktar in _aktif(tuketim, "Soğutucu & F-Gaz (Scope 1)").items():
        rows.append({
            "Enerji Kaynağı": alt_tur,
            "Kategori": "Soğutucu & F-Gaz",
            "Birim": "kg",
            "Tüketim": miktar,
            "Yenilenebilir": "Hayır",
        })
    # Araç Filosu & İş Seyahatleri
    for alt_tur, miktar in _aktif(tuketim, "Araç Filosu & İş Seyahatleri (Scope 1/3)").items():
        rows.append({
            "Enerji Kaynağı": alt_tur,
            "Kategori": "Araç Filosu & Seyahat",
            "Birim": "L / km",
            "Tüketim": miktar,
            "Yenilenebilir": "Hayır",
        })
    if not rows:
        return pd.DataFrame(columns=["Enerji Kaynağı", "Kategori", "Birim", "Tüketim", "Yenilenebilir"])

    toplam = sum(r["Tüketim"] for r in rows)
    yen_oran = (yenilenebilir_kwh / toplam * 100) if toplam > 0 else 0.0
    rows.append({
        "Enerji Kaynağı": "TOPLAM",
        "Kategori": "",
        "Birim": "",
        "Tüketim": toplam,
        "Yenilenebilir": f"{yen_oran:.1f}% yenilenebilir (elektrik bazında)",
    })
    return pd.DataFrame(rows)


def tablo12_su(tuketim, dolu_oda_gun=0, musteri=0):
    """Su Sarfiyatı Takip Tablosu (kişi/oda başına normalize)."""
    rows = []
    for alt_tur, miktar in _aktif(tuketim, SU_KATEGORI).items():
        rows.append({
            "Kaynak": alt_tur,
            "Tüketim (m³)": miktar,
            "Oda-Gün Başına (L)": round(miktar * 1000 / dolu_oda_gun, 1) if dolu_oda_gun > 0 else 0,
            "Müşteri Başına (L)": round(miktar * 1000 / musteri, 1) if musteri > 0 else 0,
        })
    if rows:
        toplam = sum(r["Tüketim (m³)"] for r in rows)
        rows.append({
            "Kaynak": "TOPLAM",
            "Tüketim (m³)": toplam,
            "Oda-Gün Başına (L)": round(toplam * 1000 / dolu_oda_gun, 1) if dolu_oda_gun > 0 else 0,
            "Müşteri Başına (L)": round(toplam * 1000 / musteri, 1) if musteri > 0 else 0,
        })
    return pd.DataFrame(rows)


def tablo13_atik(tuketim):
    """Katı Atık Takip Tablosu (türe göre, bertaraf yöntemi)."""
    rows = []
    for alt_tur, miktar in _aktif(tuketim, ATIK_KATEGORI).items():
        faktor = EMISSION_FACTORS[ATIK_KATEGORI].get(alt_tur, 0.0)
        rows.append({
            "Atık Türü": alt_tur,
            "Miktar (kg)": miktar,
            "Bertaraf Yöntemi": ATIK_BERTARAF.get(alt_tur, "Belirsiz"),
            "Emisyon (kgCO₂e)": round(miktar * faktor, 2),
        })
    if rows:
        toplam_kg = sum(r["Miktar (kg)"] for r in rows)
        toplam_co2 = sum(r["Emisyon (kgCO₂e)"] for r in rows)
        geri_donusum = sum(r["Miktar (kg)"] for r in rows
                           if r["Bertaraf Yöntemi"] in ("Geri dönüşüm", "Kompost / biyolojik"))
        rows.append({
            "Atık Türü": "TOPLAM",
            "Miktar (kg)": toplam_kg,
            "Bertaraf Yöntemi": f"%{geri_donusum / toplam_kg * 100:.1f} geri kazanımlı" if toplam_kg > 0 else "",
            "Emisyon (kgCO₂e)": round(toplam_co2, 2),
        })
    return pd.DataFrame(rows)


def kimyasal_envanter(tuketim):
    """Kimyasal Tüketim Envanteri (D2.5 altyapısı)."""
    rows = []
    for alt_tur, miktar in _aktif(tuketim, KIMYASAL_KATEGORI).items():
        faktor = EMISSION_FACTORS[KIMYASAL_KATEGORI].get(alt_tur, 0.0)
        rows.append({
            "Kimyasal": alt_tur,
            "Tüketim (L)": miktar,
            "Birim EF (kgCO₂e/L)": faktor,
            "Emisyon (kgCO₂e)": round(miktar * faktor, 2),
        })
    return pd.DataFrame(rows)


def tablo6_ekip(tesis=None):
    """Tablo 6 - Sürdürülebilirlik Ekibi Görev Listesi (TGA şablon). Deterministik şablon."""
    rows = [
        {"Görev / Sorumluluk": "Sürdürülebilirlik Koordinasyonu", "Sorumlu": "Genel Müdür / GM Yardımcısı", "Sıklık": "Aylık", "Açıklama": "Strateji, bütçe ve rapor onayı"},
        {"Görev / Sorumluluk": "Enerji & Karbon Takibi", "Sorumlu": "Teknik Müdür", "Sıklık": "Aylık", "Açıklama": "TGA Tablo 10-11 verilerinin toplanması ve doğrulanması"},
        {"Görev / Sorumluluk": "Su & Atık Takibi", "Sorumlu": "Kat Hizmetleri / Housekeeping", "Sıklık": "Aylık", "Açıklama": "Tablo 12-13 ve kimyasal envanter"},
        {"Görev / Sorumluluk": "Satın Alma & Tedarikçi Değerlendirme", "Sorumlu": "Satın Alma Müdürü", "Sıklık": "Çeyreklik", "Açıklama": "Tablo 7 - sürdürülebilir tedarik kriterleri"},
        {"Görev / Sorumluluk": "Personel Eğitimleri", "Sorumlu": "İK / Sürdürülebilirlik Elçisi", "Sıklık": "Çeyreklik", "Açıklama": "Eğitim kayıtları ve farkındalık anketleri"},
        {"Görev / Sorumluluk": "Misafir İletişimi", "Sorumlu": "Ön Büro / Pazarlama", "Sıklık": "Sürekli", "Açıklama": "Broşür, QR, sosyal medya ve anket"},
        {"Görev / Sorumluluk": "İç Denetim & Düzeltici Faaliyet", "Sorumlu": "Kalite Müdürü", "Sıklık": "Yarıyıllık", "Açıklama": "Hedef takibi ve iyileştirme planı"},
    ]
    if tesis and tesis.get("ad"):
        rows[0]["Açıklama"] += f" — {tesis['ad']}"
    return pd.DataFrame(rows)


def tablo7_tedarikci(tuketim=None):
    """Tablo 7 - Tedarikçi Değerlendirme Formu (TGA şablon). Deterministik şablon + tüketimden otomatik doldurma."""
    base = [
        {"Tedarikçi Kategorisi": "Gıda", "Kriter": "Yerel / mevsimsel ürün oranı", "Puan (1-5)": "", "Not": ""},
        {"Tedarikçi Kategorisi": "Gıda", "Kriter": "Sertifikalı ürün (organik/MSC vb.)", "Puan (1-5)": "", "Not": ""},
        {"Tedarikçi Kategorisi": "Kimyasal", "Kriter": "Çevre etiketli / biyobozunur ürün", "Puan (1-5)": "", "Not": ""},
        {"Tedarikçi Kategorisi": "Enerji", "Kriter": "YEK-G / yenilenebilir tedarik", "Puan (1-5)": "", "Not": ""},
        {"Tedarikçi Kategorisi": "Atık Yönetimi", "Kriter": "Lisanslı bertaraf / geri dönüşüm", "Puan (1-5)": "", "Not": ""},
        {"Tedarikçi Kategorisi": "Genel", "Kriter": "Sürdürülebilirlik politikası beyanı", "Puan (1-5)": "", "Not": ""},
    ]
    return pd.DataFrame(base)


def tum_tablolar(sonuc, period=""):
    """Tüm TGA tablolarını sözlük olarak döner. sonuc: {tesis, tuketim, scope, metrikler, ...}"""
    tesis = sonuc["tesis"]
    tuketim = sonuc["tuketim"]
    dolu = tesis.get("dolu_oda_gun", 0)
    musteri = tesis.get("musteri", 0)
    metrik = sonuc.get("metrikler", {})
    scope = sonuc.get("scope", {})

    donem = format_donem(period) if period else ""

    ozet_rows = [
        {"Gösterge": "Dönem", "Değer": donem},
        {"Gösterge": "Toplam Emisyon (kgCO₂e)", "Değer": metrik.get("toplam_kg", 0)},
        {"Gösterge": "Toplam Emisyon (ton)", "Değer": metrik.get("toplam_ton", 0)},
        {"Gösterge": "Oda-Gün Başına (kg)", "Değer": metrik.get("oda_gun_kg", 0)},
        {"Gösterge": "m² Başına Aylık (kg)", "Değer": metrik.get("m2_aylik_kg", 0)},
        {"Gösterge": "Müşteri Başına (kg)", "Değer": metrik.get("musteri_kg", 0)},
        {"Gösterge": "Personel Başına (kg)", "Değer": metrik.get("personel_kg", 0)},
        {"Gösterge": "Scope 1 (kgCO₂e)", "Değer": metrik.get("scope1_kg", 0)},
        {"Gösterge": "Scope 2 (kgCO₂e)", "Değer": metrik.get("scope2_kg", 0)},
        {"Gösterge": "Scope 3 (kgCO₂e)", "Değer": metrik.get("scope3_kg", 0)},
    ]

    return {
        "Ozet": pd.DataFrame(ozet_rows),
        "Tablo6_Ekip": tablo6_ekip(tesis),
        "Tablo7_Tedarikci": tablo7_tedarikci(tuketim),
        "Tablo10_Elektrik": tablo10_elektrik(tuketim),
        "Tablo11_Enerji": tablo11_enerji(tuketim),
        "Tablo12_Su": tablo12_su(tuketim, dolu, musteri),
        "Tablo13_Atik": tablo13_atik(tuketim),
        "Kimyasal_Envanter": kimyasal_envanter(tuketim),
    }
