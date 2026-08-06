# ============================================
# KarbonAT - İçerik Merkezi (Content Engine v2)
# Sürdürülebilirlik içerik türleri, amaca göre gruplar,
# planlanan yapılar, tasarım tercihleri ve AI'a hazır katman.
#
# MİMARİ (GPT dönütü uyumlu):
#   Veriler -> Content Engine -> Şablonlar -> Çıktılar
#   Aynı veri havuzu, onlarca farklı formatta (PDF/Web/QR/Sosyal).
#
# NOT: Üretim ai_engine üzerinden AKTİF. GENERATORLAR registry ileride
# tür başına özel fonksiyonlar için tutulur; şu an medya üretimi
# ai_engine.uretim_olustur'a bağlıdır. Raporlama raporlar.py'dedir.
# ============================================

# Amaca göre gruplar (İçerik Merkezi üst sekmeleri)
AMAC_GRUPLARI = [
    {"id": "raporlama", "emoji": "📄", "baslik": "Raporlama"},
    {"id": "iletisim", "emoji": "🌐", "baslik": "İletişim"},
    {"id": "politikalar", "emoji": "📋", "baslik": "Politikalar"},
    {"id": "egitim_anket", "emoji": "🎓", "baslik": "Eğitim & Anket"},
]

ICERIK_TURLERI = [
    {
        "id": "rapor",
        "sistem": "rapor",
        "grup": "raporlama",
        "emoji": "📄",
        "baslik": "Sürdürülebilirlik Raporu",
        "ciktilar": ["PDF", "Excel", "Web"],
        "aciklama": (
            "Tesisin gerçek tüketim verilerinden üretilecek resmî sürdürülebilirlik raporu. "
            "Yönetim mesajı, karbon/su/atık performansı, hedefler ve TGA tablo referanslarını içerecek."
        ),
    },
    {
        "id": "web",
        "sistem": "medya",
        "grup": "iletisim",
        "emoji": "🌐",
        "baslik": "Web Sayfası İçeriği",
        "ciktilar": ["Web", "PDF"],
        "aciklama": (
            "Otel web sitesindeki sürdürülebilirlik sayfası için hazır metin, KPI bloğu ve görsel yapı. "
            "A6 Doğru Tanıtım kurallarına uygun, gerçek veriye dayalı iddialar."
        ),
    },
    {
        "id": "brosur",
        "sistem": "medya",
        "grup": "iletisim",
        "emoji": "📖",
        "baslik": "Misafir Broşürü",
        "ciktilar": ["PDF", "Web"],
        "aciklama": (
            "1 sayfalık misafir broşürü (PDF). Çift dilli tasarım, istatistik vurgulu, "
            "QR ile veri doğrulama."
        ),
    },
    {
        "id": "qr",
        "sistem": "medya",
        "grup": "iletisim",
        "emoji": "📱",
        "baslik": "QR / Oda Kartı",
        "ciktilar": ["QR", "PDF"],
        "aciklama": (
            "Oda kapı kartı boyutunda QR içerikli kart. Kısa mesaj + öne çıkan istatistik + "
            "sürdürülebilirlik sayfasına yönlendirme."
        ),
    },
    {
        "id": "basin_bulteni",
        "sistem": "medya",
        "grup": "iletisim",
        "emoji": "📰",
        "baslik": "Basın Bülteni",
        "ciktilar": ["PDF", "Web", "Medya"],
        "aciklama": (
            "Tesisin sürdürülebilirlik başarılarını medyaya sunmak için basın bülteni taslağı; "
            "somut rakamlar ve yönetim görüşü içerir."
        ),
    },
    {
        "id": "sosyal_medya",
        "sistem": "medya",
        "grup": "iletisim",
        "emoji": "📣",
        "baslik": "Sosyal Medya",
        "ciktilar": ["Instagram", "LinkedIn", "X"],
        "aciklama": (
            "Instagram, LinkedIn ve X için platform bazında içerik paketi; gönderi metinleri, "
            "hashtag setleri ve A6 uyumlu green-claims."
        ),
    },
    {
        "id": "politika",
        "sistem": "rapor",
        "grup": "politikalar",
        "emoji": "📋",
        "baslik": "Politika Özeti",
        "ciktilar": ["PDF", "Web"],
        "aciklama": (
            "1 sayfalık sürdürülebilirlik politikası özeti. TGA'nın politika metninden ilham alınarak "
            "tesis verileriyle doldurulacak."
        ),
    },
    {
        "id": "egitim",
        "sistem": "medya",
        "grup": "egitim_anket",
        "emoji": "🎓",
        "baslik": "Eğitim Kayıtları",
        "ciktilar": ["Excel", "PDF"],
        "aciklama": (
            "Personel eğitim kayıtları modülü (A4). Eğitim takvimi, katılımcı listesi ve sertifika kaydı."
        ),
    },
    {
        "id": "gorsel_afis",
        "sistem": "medya",
        "grup": "iletisim",
        "emoji": "🎨",
        "baslik": "Görsel & Afiş",
        "ciktilar": ["Poster", "Sosyal", "Kart"],
        "aciklama": (
            "Pazarlama görselleri için AI image-prompt üretici (Flux/Midjourney). Amaç, "
            "hedef kitle, ton, görsel tema ve metin yönlendirmesi alır → görsel prompt "
            "metni ve eşlik eden pazarlama metni üretir. Şimdilik iskelettir."
        ),
    },
    {
        "id": "anket_misafir",
        "sistem": "medya",
        "grup": "egitim_anket",
        "alt_grup": "anket",
        "alt_baslik": "Misafir Anketi",
        "emoji": "📊",
        "baslik": "Anket Şablonu",
        "ciktilar": ["PDF", "Web", "Excel"],
        "aciklama": (
            "Misafir memnuniyet + sürdürülebilirlik anketi şablonu (A5). Kağıt veya dijital sunuma "
            "hazır soru seti."
        ),
    },
    {
        "id": "anket_personel",
        "sistem": "medya",
        "grup": "egitim_anket",
        "alt_grup": "anket",
        "alt_baslik": "Personel Anketi",
        "emoji": "📊",
        "baslik": "Anket Şablonu",
        "ciktilar": ["PDF", "Web", "Excel"],
        "aciklama": (
            "Personel sürdürülebilirlik farkındalığı ve eğitim geri bildirim anketi şablonu (A4)."
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
    "basin_bulteni": [
        "Başlık / manşet",
        "Spot paragraf (özet)",
        "Tesis & sürdürülebilirlik bilgileri",
        "Somut rakamlar ve başarılar",
        "Yönetimden alıntı (quote)",
        "Medya iletişim bilgileri",
    ],
    "sosyal_medya": [
        "Platforma göre gönderi metinleri (Instagram/LinkedIn/X)",
        "Hashtag setleri",
        "Görsel alt yazıları",
        "Aylık içerik takvimi",
        "Green-claim uyarı notu (A6)",
    ],
    "gorsel_afis": [
        "Ana kompozisyon — manzara, objeler, yerleşim (odak)",
        "Renk paleti ve ışık / atmosfer",
        "Metin & slogan yerleşimi (poster-sosyal-kart varyantları)",
        "Stil rehberi (fotorealist / illüstrasyon / minimal-marka)",
        "Amaç tarafına uyan örnek prompt + tesis verisi ekleme önerisi",
        "Eşlik eden pazarlama alt yazısı (opsiyonel)",
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

# Ortak tasarım tercihleri (GPT'nin 7 adımlı akışı; her türde)
ORTAK_SORULAR = [
    {
        "anahtar": "amac",
        "soru": "🎯 Amaç",
        "secenekler": ["Bilgilendirme", "Pazarlama", "Denetim", "Eğitim"],
    },
    {
        "anahtar": "hedef_kitle",
        "soru": "👥 Hedef Kitle",
        "secenekler": ["Misafir", "Denetçi", "Personel", "Yönetim", "Tedarikçi", "Yatırımcı"],
    },
    {
        "anahtar": "ton",
        "soru": "Ton & Ses",
        "secenekler": [
            "Kurumsal & Resmi", "Sıcak & Samimi", "Modern & Enerjik",
            "Sade & Şeffaf", "Lüks & Zarif", "Teknik & Detaylı",
        ],
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
    "basin_bulteni": [
        {
            "anahtar": "kapsam",
            "soru": "Bülten Kapsamı",
            "secenekler": ["Yeni başarı duyurusu", "Yıllık sonuç özeti", "Genel tanıtım"],
        },
    ],
    "sosyal_medya": [
        {
            "anahtar": "platform",
            "soru": "Öncelikli Platform",
            "secenekler": ["Instagram", "LinkedIn", "X", "Tümü"],
        },
        {
            "anahtar": "icerik_turu",
            "soru": "İçerik Türü",
            "secenekler": ["İstatistik paylaşımı", "Hikaye / arka plan", "Etkinlik duyurusu", "Karma"],
        },
    ],
    "gorsel_afis": [
        {
            "anahtar": "format",
            "soru": "Uygulama Formatı",
            "secenekler": ["Poster (A3/A4)", "Sosyal medya (1:1 / 9:16 / 4:5)", "Oda kapı kartı"],
        },
        {
            "anahtar": "stil",
            "soru": "Görsel Stil",
            "secenekler": ["Fotorealist", "Minimal / modern", "İllüstrasyon", "Otel markasına uyarlansın"],
        },
        {
            "anahtar": "odak",
            "soru": "Görsel Odak",
            "secenekler": ["Doğa & çevre", "Tesis & otel", "İnsan & topluluk", "Veri / istatistik"],
        },
        {
            "anahtar": "metin_var",
            "soru": "Metin / Slogan",
            "secenekler": ["Kısa slogan", "Başlık + alt başlık", "Metinsiz (saf görsel)"],
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

# Generator registry — üretim katmanı DEAKTİF.
# Her girdi, ilgili türün üretici fonksiyonuna bağlanınca aktifleşir.
# İmza:  generator(tesis: dict, sonuc: dict | None, prefs: dict) -> bytes
GENERATORLAR = {
    "rapor": None,
    "web": None,
    "brosur": None,
    "qr": None,
    "basin_bulteni": None,
    "sosyal_medya": None,
    "politika": None,
    "egitim": None,
    "anket_misafir": None,
    "anket_personel": None,
    "gorsel_afis": None,
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
        "amac": "Bilgilendirme",
        "hedef_kitle": "Misafir",
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


def generator_aktif_mi(tur_id):
    """İlgili türün üreticisi bağlı mı (üretim aktif mi)?"""
    return bool(GENERATORLAR.get(tur_id))
