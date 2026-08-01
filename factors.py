# ============================================
# KarbonAT P2 - Emisyon Faktörleri
# Kaynak: HCMI v2.0, GHG Protocol, Türkiye Grid EF
# ============================================

# Türkiye şebeke elektriği emisyon faktörü (kgCO₂e/kWh)
# Kaynak: TEİAş / EPDK 2024 ortalama grid mix
TURKIYE_GRID_EF = 0.478  # kgCO₂e/kWh

# Yenilenebilir enerji için (Güneş, Rüzgar, Hidro)
YENILENEBILIR_ELEKTRIK_EF = 0.0  # sıfır emisyon (yenilenebilir)

EMISSION_FACTORS = {
    "Elektrik": {
        "Şebeke (yenilenebilir olmayan)": TURKIYE_GRID_EF,  # kgCO₂e/kWh
        "Şebeke (yenilenebilir YEK-G sertifikalı)": YENILENEBILIR_ELEKTRIK_EF,
        "Güneş Enerjisi (PV)": 0.045,  # kgCO₂e/kWh (yaşam döngüsü)
        "Rüzgar Enerjisi": 0.013,  # kgCO₂e/kWh
    },
    "Doğal Gaz": {
        # kgCO₂e/m³ (yakma emisyonu — Scope 1)
        "Doğalgaz (m³)": 2.02,
        "LNG (m³)": 2.75,
        "LPG (kg)": 2.94,  # kgCO₂e/kg
        "Propan (m³)": 2.98,
        "Kömür (ton)": 2.420,  # kgCO₂e/kg (ton başına, hesaplama için ton girilir)
    },
    "Su": {
        # Scope 3 - su arıtma ve atık su işleme
        "Şebeke suyu tüketimi (m³)": 0.422,  # kgCO₂e/m³
        "Deniz suyu (m³)": 1.5,
        "Atık su arıtma (m³)": 0.8,
    },
    "Gıda Tüketimi": {
        # Scope 3 - tedarik zinciri emisyonları
        "Kırmızı Et (kg)": 27.0,
        "Tavuk (kg)": 6.0,
        "Balık (kg)": 5.0,
        "Sebze (kg)": 2.0,
        "Süt (kg)": 1.5,
        "Peynir (kg)": 10.0,
        "Ekmek & Unlu Mamul (kg)": 1.0,
    },
    "Atık Yönetimi": {
        # Scope 3 - bertaraf emisyonları
        "Organik Atık (kg)": 0.5,
        "Plastik Atık (kg)": 3.5,
        "Cam (kg)": 0.33,
        "Kağıt (kg)": 0.2,
        "Metal (kg)": 2.0,
    },
    "Kimyasal Tüketimi": {
        # Scope 3 - üretim emisyonları
        "Deterjan (L)": 0.5,
        "Yumuşatıcı (L)": 0.3,
        "pH Düzenleyici (L)": 1.5,
        "Temizlik Ürünleri (L)": 0.75,
    },
}

# Kullanıcıya gösterilecek açıklamalar
KATEGORI_ACIKLAMALARI = {
    "Elektrik": "Türkiye şebeke ortalaması 0,478 kgCO₂e/kWh kullanılmıştır. YE-G sertifikalı elektrik sıfır emisyon kabul edilir.",
    "Doğal Gaz": "Yerinde yakma (Scope 1) emisyonlarıdır. Birimler kcal/kg veya m³ bazında olabilir.",
    "Su": "Şebeke suyu arıtma + atık su arıtma emisyonları dahildir (Scope 3).",
    "Gıda Tüketimi": "Tedarik zinciri emisyonları (Scope 3). Hayvansal ürünlerin emisyonu yüksektir.",
    "Atık Yönetimi": "Atık bertaraf süreçlerinin salımı (Scope 3). Geri dönüşümle azalır.",
    "Kimyasal Tüketimi": "Kimyasal üretim süreci emisyonları (Scope 3). Deterjan, yumuşatıcı, havuz kimyasalları.",
}


# ============================================
# SCOPE ATAMASI (HCMI Metodolojisi)
# ============================================
# Scope 1: Doğrudan yakma (fosil yakıt, doğalgaz, kömür)
# Scope 2: Satın alınan elektrik
# Scope 3: Gıda, su arıtma, atık bertaraf, kimyasal

SCOPE_ATAMASI = {
    "Elektrik": "scope2",   # tüm elektrik kalemleri scope 2
    "Doğal Gaz": "scope1",  # yerinde yakma
    "Su": "scope3",        # su arıtma emisyonu
    "Gıda Tüketimi": "scope3",
    "Atık Yönetimi": "scope3",
    "Kimyasal Tüketimi": "scope3",
}


def kullanim_birimleri_kg_co2(kategori, alt_tur):
    """Verilen kategori+tür için kgCO2e birim değerini döner."""
    return EMISSION_FACTORS.get(kategori, {}).get(alt_tur, 0.0)
