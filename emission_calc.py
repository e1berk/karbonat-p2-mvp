# ============================================
# KarbonAT P2 - Hesaplama Motoru
# HCMI Metodolojisi + 4 Normalize Metrik
# ============================================

from factors import EMISSION_FACTORS, SCOPE_ATAMASI


def hesapla_scope_ayrimi(tuketim_dict):
    """
    Girdi: {kategori: {alt_tür: miktar}} formatında tüketim.
    Çıktı: scope1/scope2/scope3 dağılımı + kategori toplamları.
    """
    scope_toplamlari = {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0}
    kategori_toplamlari = {}

    for kategori, alt_turler in tuketim_dict.items():
        kategori_emisyon = 0.0
        scope_key = SCOPE_ATAMASI.get(kategori, "scope3")

        for alt_tur, miktar in alt_turler.items():
            if miktar is None or miktar <= 0:
                continue
            faktor = EMISSION_FACTORS.get(kategori, {}).get(alt_tur, 0.0)
            emisyon = miktar * faktor
            kategori_emisyon += emisyon
            scope_toplamlari[scope_key] += emisyon

        kategori_toplamlari[kategori] = kategori_emisyon

    toplam = sum(scope_toplamlari.values())

    return {
        "scope1": scope_toplamlari["scope1"],
        "scope2": scope_toplamlari["scope2"],
        "scope3": scope_toplamlari["scope3"],
        "toplam": toplam,
        "kategori_toplamlari": kategori_toplamlari,
    }


def hesapla_normalize_metrikler(toplam_kg, m2, oda, personel, musteri, dolu_oda_gun):
    """
    4 temel normalize metrik — HCMI endüstri standardı:
      1) Toplam emisyon (kg / ton)
      2) Dolu oda-gün başına (kg per occupied room-night)
      3) m² başına aylık (kg per m² per month)
      4) Müşteri başına (kg per customer)
    """
    # Ton cinsinden (daha okunur)
    toplam_ton = round(toplam_kg / 1000, 2)

    # 1. Dolu oda-gün başına (HCMI primary metric)
    oda_gun_kg = round(toplam_kg / dolu_oda_gun, 2) if dolu_oda_gun > 0 else 0

    # 2. m² başına aylık
    m2_aylik_kg = round(toplam_kg / m2, 2) if m2 > 0 else 0

    # 3. Müşteri (tur) başına
    musteri_kg = round(toplam_kg / musteri, 2) if musteri > 0 else 0

    # 4. Personel başına (yardımcı metrik)
    personel_kg = round(toplam_kg / personel, 2) if personel > 0 else 0

    return {
        "toplam_kg": round(toplam_kg, 2),
        "toplam_ton": toplam_ton,
        "oda_gun_kg": oda_gun_kg,
        "m2_aylik_kg": m2_aylik_kg,
        "musteri_kg": musteri_kg,
        "personel_kg": personel_kg,
        "scope1_kg": 0,  # Sonuç sonradan doldurulur
        "scope2_kg": 0,
        "scope3_kg": 0,
    }


def metrikleri_scope_ile_zenginlestir(metrikler, scope_data):
    """Scope dağılımını metrik sözlüğüne ekler."""
    metrikler["scope1_kg"] = round(scope_data["scope1"], 2)
    metrikler["scope2_kg"] = round(scope_data["scope2"], 2)
    metrikler["scope3_kg"] = round(scope_data["scope3"], 2)
    return metrikler


def en_agir_kaynaklar(kategori_toplamlari, n=3):
    """
    En yüksek emisyonlu kategorileri sıralar.
    [(kategori, kgCO2, yüzde), ...]
    """
    toplam = sum(kategori_toplamlari.values())
    sirali = sorted(kategori_toplamlari.items(), key=lambda x: x[1], reverse=True)[:n]
    return [
        (kategori, deger, round((deger / toplam * 100) if toplam > 0 else 0, 1))
        for kategori, deger in sirali
    ]


def format_kg_co2(kg):
    """Görsel format: 1234 → 1,234 kg"""
    return f"{kg:,.2f}"
