# ============================================
# KarbonAT - İçerik Merkezi (İskelet v1)
# Sürdürülebilirlik içerik türleri, planlanan yapılar,
# tasarım tercihleri ve AI'a hazır tercih katmanı.
#
# NOT: Üretim/indirme katmanı şimdilik DEAKTİF.
# İçerik metinleri araştırma tamamlanınca (ileride AI destekli)
# bu tercih yapısından otomatik üretilecek.
# ============================================

ICERIK_TURLERI = [
    {
        "id": "rapor",
        "emoji": "📄",
        "baslik": "Sürdürülebilirlik Raporu",
        "aciklama": (
            "Tesisin gerçek tüketim verilerinden üretilecek resmî sürdürülebilirlik raporu. "
            "Yönetim mesajı, karbon/su/atık performansı, hedefler ve TGA tablo referanslarını içerecek."
        ),
    },
    {
        "id": "web",
        "emoji": "🌐",
        "baslik": "Web Sayfası İçeriği",
        "aciklama": (
            "Otel web sitesindeki sürdürülebilirlik sayfası için hazır metin, KPI bloğu ve görsel yapı. "
            "A6 Doğru Tanıtım kurallarına uygun, gerçek veriye dayalı iddialar."
        ),
    },
    {
        "id": "brosur",
        "emoji": "📖",
        "baslik": "Misafir Broşürü",
        "aciklama": (
            "1 sayfalık misafir broşürü (PDF). Çift dilli tasarım, istatistik vurgulu, "
            "QR ile veri doğrulama."
        ),
    },
    {
        "id": "qr",
        "emoji": "📱",
        "baslik": "QR / Oda Kartı",
        "aciklama": (
            "Oda kapı kartı boyutunda QR içerikli kart. Kısa mesaj + öne çıkan istatistik + "
            "sürdürülebilirlik sayfasına yönlendirme."
        ),
    },
    {
        "id": "politika",
        "emoji": "📋",
        "baslik": "Politika Özeti",
        "aciklama": (
            "1 sayfalık sürdürülebilirlik politikası özeti. TGA'nın politika metninden ilham alınarak "
            "tesis verileriyle doldurulacak."
        ),
    },
    {
        "id": "anket_misafir",
        "emoji": "📊",
        "baslik": "Anket Şablonu",
        "grup": "anket",
        "alt_baslik": "Misafir Anketi",
        "aciklama": (
            "Misafir memnuniyet + sürdürülebilirlik anketi şablonu (A5). Kağıt veya dijital sunuma "
            "hazır soru seti."
        ),
    },
    {
        "id": "anket_personel",
        "emoji": "📊",
        "baslik": "Anket Şablonu",
        "grup": "anket",
        "alt_baslik": "Personel Anketi",
        "aciklama": (
            "Personel sürdürülebilirlik farkındalığı ve eğitim geri bildirim anketi şablonu (A4)."
        ),
    },
    {
        "id": "egitim",
        "emoji": "🎓",
        "baslik": "Eğitim Kayıtları",
        "aciklama": (
            "Personel eğitim kayıtları modülü (A4). Eğitim takvimi, katılımcı listesi ve sertifika kaydı."
        ),
    },
]

ISKELETLER = {
    "rapor": [
        "Kapak — tesis adı, logo, dönem ve ton CO₂e özeti",
        "Yönetim Mesajı",
        "Yöntem & Kapsam (hesaplama standardı, HCMI)",
        "Enerji & Karbon (ton CO₂e, yenilenebilir oranı)",
        "Su Yönetimi (m³, kişi/oda-gün başına)",
        "Atık & Geri Dönüşüm (kg, geri kazanım %)",
        "Tedarik & Yerel Satın Alma",
        "Topluluk & Sosyal Etki",
        "Hedefler & Aksiyon Planı",
        "Ekler — TGA Tablo 10-13 referansları",
    ],
    "web": [
        "Başlık + slogan",
        "Tanıtım paragrafı (tesis hikayesi)",
        "Sayılarla etkimiz — KPI bloğu (ton CO₂e, su m³, geri dönüşüm %)",
        "Enerji / Su / Atık detay bölümleri",
        "Misafirlere yönelik ipuçları",
        "Sertifika & doğrulama rozetleri",
        "İletişim / QR yönlendirmesi",
    ],
    "brosur": [
        "Kapak — tesis adı + öne çıkan iddia",
        "Biz kimiz — sürdürülebilirlik hikayemiz",
        "Enerji & Karbon (sayılarla)",
        "Su & Atık (tasarruf + geri kazanım %)",
        "Yerel & Topluluk",
        "Misafirlerin yapabilecekleri (ipuçları)",
        "QR / iletişim",
    ],
    "qr": [
        "Kart ön yüz — tesis adı + logo + kısa iddia",
        "QR kod (web sürdürülebilirlik sayfası)",
        "Arka yüz — 3-4 ikon + sayı (enerji/su/atık)",
        "Dil seçeneği (TR/EN)",
    ],
    "politika": [
        "Amaç & Kapsam",
        "Taahhüt maddeleri (çevre, topluluk, misafir, çalışan)",
        "Sorumluluk & Uygulama",
        "İzleme & Raporlama",
        "İletişim",
    ],
    "anket_misafir": [
        "Giriş — misafiri selamlama + tahmini süre",
        "Genel memnuniyet soruları",
        "Sürdürülebilirlik farkındalık soruları",
        "Konaklama uygulamaları geri bildirimi",
        "Açık uçlu yorum alanı",
        "Teşekkür + geri bildirim teşviki",
    ],
    "anket_personel": [
        "Giriş — anket amacı ve gizlilik notu",
        "Sürdürülebilirlik farkındalığı",
        "Eğitim geri bildirimi",
        "İşyeri pratikleri önerileri",
        "Açık uçlu yorum alanı",
    ],
    "egitim": [
        "Eğitim takvimi (tarih, konu, eğitmen)",
        "Katılımcı listesi (isim, bölüm)",
        "Eğitim süresi & konu kategorisi",
        "Sertifika / imza kaydı",
        "A4 kriteriyle bağlantı",
    ],
}

# Ortak tasarım tercihleri (her türde)
ORTAK_SORULAR = [
    {
        "anahtar": "ton",
        "soru": "Ton & Ses",
        "secenekler": ["Kurumsal & Resmi", "Sıcak & Samimi", "Modern & Enerjik", "Sade & Şeffaf"],
    },
    {
        "anahtar": "dil",
        "soru": "Dil",
        "secenekler": ["Türkçe", "İngilizce", "Türkçe + İngilizce"],
    },
    {
        "anahtar": "vurgu",
        "soru": "Ana Vurgu",
        "secenekler": ["Çevre & İklim", "Topluluk & Yerel", "Misafir Deneyimi", "Yerel Kültür"],
    },
    {
        "anahtar": "uzunluk",
        "soru": "Uzunluk",
        "secenekler": ["Kısa (özet)", "Orta", "Detaylı"],
    },
]

# Türe özel tasarım tercihleri
TURE_OZEL_SORULAR = {
    "rapor": [
        {
            "anahtar": "kapsam",
            "soru": "Rapor Kapsamı",
            "secenekler": ["Sadece Çevre", "Çevre + Topluluk", "Tam GSTC Kriterleri"],
        },
        {
            "anahtar": "istatistik",
            "soru": "İstatistik Yoğunluğu",
            "secenekler": ["Grafik ağırlıklı", "Metin ağırlıklı", "Dengeli"],
        },
    ],
    "web": [
        {
            "anahtar": "bolumler",
            "soru": "Sayfa Bölümleri",
            "secenekler": ["Başlık + metin", "+ İstatistik bloğu", "+ Misafir ipuçları", "+ Medya/galeri"],
        },
    ],
    "brosur": [
        {
            "anahtar": "kitle",
            "soru": "Hedef Kitle",
            "secenekler": ["Misafir odaklı", "Kurumsal / B2B odaklı", "Her ikisi"],
        },
        {
            "anahtar": "istatistik",
            "soru": "İstatistik Yoğunluğu",
            "secenekler": ["Sayılarla anlat", "Hikaye odaklı", "Dengeli"],
        },
    ],
    "qr": [
        {
            "anahtar": "kart_icerik",
            "soru": "Kart İçeriği",
            "secenekler": ["Kısa mesaj + QR", "İstatistik + QR", "İkon listesi + QR"],
        },
        {
            "anahtar": "qr_hedef",
            "soru": "QR Hedefi",
            "secenekler": ["Web sürdürülebilirlik sayfası", "Yeşil rapor", "İletişim"],
        },
    ],
    "politika": [
        {
            "anahtar": "kapsam",
            "soru": "Politika Kapsamı",
            "secenekler": ["Tek başlık özet", "2-3 konu", "Tüm GSTC konuları"],
        },
    ],
    "anket_misafir": [
        {
            "anahtar": "konular",
            "soru": "Anket Konuları",
            "secenekler": ["Genel memnuniyet + sürdürülebilirlik", "Sadece sürdürülebilirlik", "Konaklama + ulaşım"],
        },
        {
            "anahtar": "olcek",
            "soru": "Ölçek Tipi",
            "secenekler": ["1-5 yıldız", "Smiley / ikon", "Evet-Hayır + yorum"],
        },
        {
            "anahtar": "soru_sayisi",
            "soru": "Soru Sayısı",
            "secenekler": ["Kısa (5-8)", "Orta (8-12)", "Detaylı (12+)"],
        },
    ],
    "anket_personel": [
        {
            "anahtar": "konular",
            "soru": "Anket Konuları",
            "secenekler": ["Sürdürülebilirlik farkındalığı", "Eğitim geri bildirimi", "İşyeri pratikleri"],
        },
        {
            "anahtar": "olcek",
            "soru": "Ölçek Tipi",
            "secenekler": ["1-5 puan", "Smiley / ikon", "Evet-Hayır + yorum"],
        },
        {
            "anahtar": "soru_sayisi",
            "soru": "Soru Sayısı",
            "secenekler": ["Kısa (5-8)", "Orta (8-12)", "Detaylı (12+)"],
        },
    ],
    "egitim": [
        {
            "anahtar": "konular",
            "soru": "Eğitim Konuları",
            "secenekler": ["Çevre & enerji", "Atık & geri dönüşüm", "Su & hijyen", "Genel sürdürülebilirlik"],
        },
        {
            "anahtar": "periyot",
            "soru": "Eğitim Periyodu",
            "secenekler": ["Aylık", "3 aylık", "Yıllık"],
        },
    ],
}

# Görsel temalar (üretim aşamasında palete uygulanacak)
TEMALAR = {
    "orman": {"ad": "🌿 Orman", "renkler": ["#1d6b45", "#2e8b57", "#3da873", "#b7d8c2"]},
    "okyanus": {"ad": "🌊 Okyanus", "renkler": ["#1b5e7b", "#2e8bb0", "#3da8c9", "#b7dce8"]},
    "toprak": {"ad": "🌾 Toprak", "renkler": ["#8a5a2b", "#b07a3d", "#d9a05b", "#ead9bd"]},
    "minimal": {"ad": "🖤 Minimal", "renkler": ["#1a1a1a", "#444444", "#777777", "#e0e0e0"]},
    "marka": {"ad": "🎨 Otel markasına uyarlansın", "renkler": []},
}


def varsayilan_tercih(tur_id):
    """Her içerik türü için varsayılan tercih sözlüğü."""
    return {
        "ton": "Kurumsal & Resmi",
        "dil": "Türkçe",
        "vurgu": "Çevre & İklim",
        "uzunluk": "Orta",
        "tema": "orman",
        "notlar": "",
    }


def tercih_sorulari(tur_id):
    """Ortak sorular + türe özel soruları döner."""
    return ORTAK_SORULAR + TURE_OZEL_SORULAR.get(tur_id, [])


def tur_bul(tur_id):
    for tur in ICERIK_TURLERI:
        if tur["id"] == tur_id:
            return tur
    return None
