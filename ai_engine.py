# ============================================
# KarbonAT - AI Üretim Katmanı (A5)
#
# RAG (data/kb.json üzerinden kosinüs benzerliği) + Gemini üretimi.
# Deterministik alanlar (hesap motoru, TGA tabloları, Excel/PDF)
# burada DEVRE DIŞIDIR; AI yalnız anlatı/broşür/politika/sosyal/
# anket/image-prompt metinleri üretir.
#
# Kullanım:
#   python ai_engine.py --soru "atık yönetimi politikası"
#   python ai_engine.py --uretim rapor
#
# Üretim modeli: GEMINI_MODEL ortam değişkeniyle ayarlanabilir;
# yoksa fallback listesi sırayla denenir (kota hatalarında sıradakine geçer).
# ============================================
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from icerik_hub import ISKELETLER, tur_bul, TURE_OZEL_SORULAR  # noqa: E402

CAKTI_YOL = Path(__file__).parent / "data" / "kb.json"
EMBED_MODEL = "gemini-embedding-001"

# Sırayla denenir: ilk çalışan kullanılır (429 kota / 404 erişim hatasında geç).
# Yeni anahtarla (Ağu 2026) test edilmiş gerçek ücretsiz metin modelleri:
#   gemini-3.7-flash ✅, gemini-3.6-flash ✅ (iki de çalıştı, canlı doğrulandı).
#   gemini-2.5-flash(-lite) / -001 sürümleri yeni kullanıcılara 404 veriyor (kapalı).
# "gemini-2.5-pro" ücretsiz katmanda yok (her zaman "limit: 0" 429).
# Not: models.list()'te görünen ancak test edilmemiş adaylar (3.5-flash,
# 3.1-flash-lite, flash-latest) ileride kota dolduğunda faydalı olursa eklenebilir.
GEN_MODELS = [
    os.environ.get("GEMINI_MODEL", ""),
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]
GEN_MODELS = [m for m in GEN_MODELS if m]


# ---------------- İstemci ----------------
def _client():
    from google import genai

    anahtar = os.environ.get("GEMINI_API_KEY", "")
    if not anahtar:
        raise RuntimeError("GEMINI_API_KEY .env içinde yok.")
    return genai.Client(api_key=anahtar)


# ---------------- RAG ----------------
def _kosinus(a: list[float], b: list[float]) -> float:
    skaler = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return skaler / (na * nb) if na and nb else 0.0


def kbs_var_mi() -> bool:
    return CAKTI_YOL.exists()


def rag_sorgu(soru: str, k: int = 4) -> list[dict]:
    """data/kb.json üzerinde kosinüs benzerliğiyle en ilgili chunk'ları döner."""
    if not kbs_var_mi():
        return []
    with open(CAKTI_YOL, encoding="utf-8") as f:
        kb = json.load(f)
    if not kb.get("chunks"):
        return []
    c = _client()
    r = c.models.embed_content(model=EMBED_MODEL, contents=soru)
    sorgu_emb = r.embeddings[0].values
    eslesmeler = []
    for ch in kb["chunks"]:
        benzerlik = _kosinus(sorgu_emb, ch["embedding"])
        eslesmeler.append((benzerlik, ch))
    eslesmeler.sort(key=lambda t: t[0], reverse=True)
    return [
        {"kaynak": ch["kaynak"], "benzerlik": round(b, 4), "metin": ch["metin"]}
        for b, ch in eslesmeler[:k]
    ]


def _sanitize(text: str, limit: int = 500) -> str:
    """Kullanıcı girdisini prompt injection'a karşı temizle ve kısalt."""
    if not text:
        return ""
    t = str(text).strip()[:limit]
    # Yaygın override ifadelerini etkisizleştir
    for pat in ["ignore previous", "önceki talimat", "sistem prompt", "system prompt", "green-claim yap", "0 emisyon yaz"]:
        t = t.replace(pat, "[filtrelendi]")
        t = t.replace(pat.upper(), "[filtrelendi]")
    # Kontrol karakterleri temizle
    t = t.replace("\n", " ").replace("\r", " ")
    return t


# ---------------- Tesis özeti (prompt için) ----------------
def _hedef_odak(tur_id: str, prefs: dict) -> str:
    """Kullanıcının seçtiği platform/hedef kitle/amaç/vurguyu AI için BAĞLAYICI talimata çevirir."""
    satirlar = []

    hedef = (prefs.get("hedef_kitle") or "Misafir").strip()
    hedef_rehber = {
        "Denetçi": (
            "Hedef: DİKKATLİ bir DENETÇİ / otorite. Veriyi ve metodolojik adımları açık, "
            "doğrulanabilir biçimde sun; yeşil iddia (green-claim) YAPMA, sayıları yuvarlama "
            "gerekçesi ve kaynağıyla ver. Ton resmî ve kanıta dayalı olmalı."
        ),
        "Misafir": (
            "Hedef: tesiste konaklayan MİSAFİR. Sıcak, kısa, anlaşılır anlat; somut rakamı "
            "hikayeleştir, yönlendirici/metodik dilden kaçın."
        ),
        "Personel": (
            "Hedef: otel PERSONELİ. Görev ve sorumluluk odaklı, uygulanabilir eylem dilinde yaz."
        ),
        "Yönetim": (
            "Hedef: otel YÖNETİMİ / karar verici. Stratejik özet, maliyet/getiri ve aksiyon "
            "vurgusu ağırlıklı olmalı."
        ),
        "Yatırımcı": (
            "Hedef: YATIRIMCI. ESG performansı, risk yönetimi ve sürdürülebilir iş modeli "
            "diliyle yaz."
        ),
    }
    satirlar.append(hedef_rehber.get(hedef.split(" ")[0], hedef_rehber["Misafir"]))

    platform = (prefs.get("platform") or "").strip()
    if tur_id == "sosyal_medya" and platform and platform != "Tümü":
        satirlar.append(
            f"PLATFORM KİLİDİ: Yalnız {platform} için üret. ### bölümlerini SADECE "
            f"{platform} için aç; diğer platformlara (Instagram/LinkedIn/X) HİÇBİR bölüm/taslak koyma."
        )

    icerik_turu = (prefs.get("icerik_turu") or "").strip()
    if icerik_turu and icerik_turu not in ("", "Karma"):
        ceviri = {
            "İstatistik paylaşımı": "İstatistik / veri odaklı paylaşım",
            "Hikaye / arka plan": "Hikaye / arka plan anlatımı",
            "Etkinlik duyurusu": "Etkinlik duyurusu",
        }.get(icerik_turu, icerik_turu)
        satirlar.append(
            f"İÇERİK KİLİDİ: Gönderi yalnız '{ceviri}' tarzında olmalı; başka gönderi türüne "
            f"kayma."
        )

    amac = (prefs.get("amac") or "").strip()
    if amac:
        satirlar.append(f"AMAÇ: İçeriğin ana amacı '{amac}' — yazı buna hizmet etsin.")

    vurgu = (prefs.get("vurgu") or "").strip()
    if vurgu:
        satirlar.append(f"VURGU: Tesisin '{vurgu}' konusunu öne çıkar.")

    ton = (prefs.get("ton") or "").strip()
    if ton:
        satirlar.append(f"TON: '{ton}'.")

    notlar = _sanitize(prefs.get("notlar") or "", limit=500)
    if notlar:
        satirlar.append(f"KULLANICI NOTU: {notlar}")

    return "\n".join(satirlar)


def _tesis_ozeti(tesis: dict, sonuc: dict | None) -> str:
    ad = _sanitize(tesis.get('ad',''), 80)
    if not sonuc:
        return (
            f"Tesis: {ad} · {tesis.get('m2','?')} m² · "
            f"{tesis.get('oda','?')} oda · {tesis.get('personel','?')} personel"
            f"\nHESAPLANMIŞ EMİSYON VERİSİ YOK: hiçbir 0/ton/sayı yazma; somut rakam "
            f"yoksa genel ve temkinli sürdürülebilirlik ifadeleriyle yaz."
        )
    m = sonuc.get("metrikler", {})
    s = sonuc.get("statik", {})
    satirlar = [
        f"Tesis: {tesis.get('ad','')} ({tesis.get('il','')}, {tesis.get('m2','?')} m², {tesis.get('oda','?')} oda, {tesis.get('personel','?')} personel)",
        f"Toplam emisyon: {m.get('toplam_ton','?')} ton CO₂e",
        f"Scope 1/2/3: {m.get('scope1_kg','?')} / {m.get('scope2_kg','?')} / {m.get('scope3_kg','?')} kg",
        f"Dolu oda-gün başına: {m.get('oda_gun_kg','?')} kg",
        f"m² başına: {m.get('m2_aylik_kg','?')} kg · müşteri başına: {m.get('musteri_kg','?')} kg",
        f"Yenilenebilir enerji oranı: {s.get('yenilenebilir','?')}%",
        f"Atık bertarafı: {s.get('atik_bertaraf','belirtilmedi')}",
    ]
    en_agir = sonuc.get("en_agir") or {}
    if isinstance(en_agir, dict):
        en_agir = list(en_agir.items())
    if en_agir:
        try:
            ilk = en_agir[:2]
            if isinstance(ilk[0], (list, tuple)) and len(ilk[0]) >= 3:
                ozet = ", ".join(f"{k} (%{y})" for k, _, y in ilk)
            else:
                ozet = ", ".join(f"{k} %{v}" for k, v in ilk)
            satirlar.append("En ağır kaynaklar: " + ozet)
        except (TypeError, ValueError, IndexError):
            pass
    return "\n".join(satirlar)


# Tür başına GÖREV talimatı — AI yalnızca kendi başlığına/amacına yanıt verir.
TUR_GOREV = {
    "web": "Yalnız otel web sitesinin 'Sürdürülebilirlik' sayfası için hazır web metni üret. Rapor, politika, sosyal medya gönderisi YAZMA.",
    "brosur": "Yalnız misafir broşürüne BASILACAK hazır metin üret: başlık, kısa bölümler, madde/istatistik vurgulu. Kapak ve bölüm başlıklarını ### ile işaretle.",
    "qr": "Yalnız oda/QR kartının ÜZERİNDE görünecek hazır metin üret: tek cümlelik ana mesaj, 3-4 ikon/sayı başlığı (örn. 'Su Tasarrufu %32'), QR doğrulama açıklaması. Talimat/prompt YAZMA.",
    "basin_bulteni": "Yalnız yayınlanmaya HAZIR basın bülteni metni üret: manşet, spot, gelişme paragrafları, yönetimden alıntı, iletişim. 'bülten şöyle olmalı' anlatımı YASAK.",
    "sosyal_medya": "Yalnız paylaşılabilecek HAZIR gönderi metinleri üret. PLATFORM TERCİHİNE UY: eğer tek platform seçilmişse SADECE onun ### bölümünü yaz, diğer platformlara bölüm AÇMA. Gönderi metni + hashtagler + görsel alt yazısı. 'şöyle yapın' anlatımı YASAK.",
    "politika": "Yalnız sürdürülebilirlik politikası özeti üret; taahhüt maddeleri ve sorumluluk. Hazır politika metni yaz, talimat değil.",
    "egitim": "Yalnız personel eğitim kayıt/planlama içeriği üret: eğitim takvimi, konular, katılımcı kaydı.",
    "gorsel_afis": "Yalnız afişe/postere BASILACAK hazır metin üret: büyük başlık, alt başlık/slogan, 3 sayı kartı, kısa bölüm metinleri, rozet ve QR yönlendirme. Image-prompt/üretim talimatı/kompozisyon tarifi KESİNLİKLE YAZMA.",
    "anket_misafir": "Yalnız misafir sürdürülebilirlik anketi soru seti üret (memnuniyet + farkındalık).",
    "anket_personel": "Yalnız personel farkındalık ve eğitim geri bildirim anketi soru seti üret.",
}

# Tür başına RAG filtre anahtarları (yalnız ilgili şablon kaynaklarından beslenir).
TUR_RAG_FILTRE = {
    "web": ["POLITIKASI", "Politika", "Raporlamasi"],
    "brosur": ["POLITIKASI", "Politika", "Raporlamasi"],
    "qr": ["Politika"],
    "basin_bulteni": ["Raporlamasi", "Politika"],
    "sosyal_medya": ["Politika", "Raporlamasi"],
    "politika": ["POLITIKASI", "Politika"],
    "egitim": ["EGITIM", "Egitim"],
    "gorsel_afis": [],
    "anket_misafir": ["Tablo 5", "Anket"],
    "anket_personel": ["Tablo 5", "Anket", "Egitim"],
}


def _rag_filtreli(soru: str, terimler: list[str], k: int = 4) -> list[dict]:
    """KB'de kosinüs araması yapar, ardından şablon kaynak adına göre filtreler."""
    sonuclar = rag_sorgu(soru, k=k * 3)
    if not terimler:
        return sonuclar[:k]
    alt = [r for r in sonuclar
           if any(t.lower() in r["kaynak"].lower() for t in terimler)]
    return (alt or sonuclar)[:k]


def _is_retryable(e: Exception) -> bool:
    s = str(e).lower()
    if "429" in s or "resource_exhausted" in s or "quota" in s or "retry" in s or "unavailable" in s or "deadline" in s or "500" in s or "503" in s:
        return True
    if "400" in s or "403" in s or "401" in s or "invalid" in s or "not found" in s or "404" in s:
        return False
    return True


def _retry_bekle(e: Exception) -> float:
    """429 yanıtındaki istediği 'retryDelay' süresini saniye olarak ayıkla.

    Gemini hata detayında `'retryDelay': '16s'` tarzı JSON/string bulunur.
    Bulunamazsa varsayılan 2 sn döner.
    """
    import re

    m = re.search(r"""retry[_-]?delay['"]?\s*[:=]\s*['"]?(\d+)""", str(e), re.I)
    if not m:
        return 2
    saniye = int(m.group(1))
    return max(2, min(saniye, 60))


def _gemini_cagir(prompt: str) -> str:
    """Model fallback'li Gemini çağrısı — markdown döner.

    Ücretsiz katmanda 429 (kota) sık olduğundan, her hata sonrası API'nin
    istediği 'retryDelay' kadar beklenir ve tüm liste tekrar denenir. Toplam
    beklemeye bir tavan konur; hâlâ kota kapalıysa açık teşhisli RuntimeError
    fırlatılır.
    """
    c = _client()
    hata = None
    beklenen = 0
    MAX_BEKLE = 90  # saniye
    while beklenen < MAX_BEKLE:
        for model in GEN_MODELS:
            try:
                r = c.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"response_mime_type": "text/plain"},
                )
                metin = (r.text or "").strip()
                if not metin:
                    raise RuntimeError("Boş yanıt")
                return metin
            except Exception as e:  # noqa: BLE001 — model fallback
                hata = e
                if not _is_retryable(e):
                    raise RuntimeError(f"Üretim hatası (yeniden denenemez): {e}") from e
                gec = _retry_bekle(e)
                beklenen += gec
                print(
                    f"  ! {model} başarısız ({type(e).__name__}); {gec}sn bekle",
                    file=sys.stderr,
                )
                if beklenen >= MAX_BEKLE:
                    break
                time.sleep(gec)
        if beklenen >= MAX_BEKLE:
            break
    raise RuntimeError(f"Tüm üretim modelleri başarısız (kota 90sn aşıldı). Son hata: {hata}")


# ---------------- Görsel Üretimi ----------------
GORSEL_MODELS = [
    os.environ.get("GEMINI_IMAGE_MODEL", ""),
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
    "gemini-3.1-flash-image",
]
GORSEL_MODELS = [m for m in GORSEL_MODELS if m]

# Ücretsiz ve anahtarsız görsel üretimi — Pollinations.ai
# https://image.pollinations.ai/prompt/{prompt}?model=flux&width=...&height=...
POLLINATIONS_IMAGE = "https://image.pollinations.ai/prompt/"
POLLINATIONS_MODEL = os.environ.get("POLLINATIONS_MODEL", "flux")


def gorsel_uret(
    tur_id: str,
    tesis: dict,
    sonuc: dict | None,
    prefs: dict,
) -> bytes:
    """Tesis verisi + tercihlere göre AI ile gerçek görsel üretir.

    Pollinations.ai (ücretsiz, anahtar gerektirmez) kullanılır. Yanıt PNG'ye
    çevrilip döndürülür. Kullanılamazsa açık teşhisli RuntimeError fırlatır.
    """
    tur = tur_bul(tur_id)
    baslik = tur["baslik"] if tur else tur_id
    prompt = _gorsel_prompt(baslik, tur_id, tesis, sonuc, prefs)

    import urllib.parse
    import urllib.request

    last_err = None
    for deneme in range(3):
        url = POLLINATIONS_IMAGE + urllib.parse.quote(prompt) + (
            f"?width=1024&height=1024&model={POLLINATIONS_MODEL}&nologo=true&seed={_rastgele_seed()}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KarbonAT/0.4 (image generator)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if data:
                break
        except Exception as e:  # noqa: BLE001
            last_err = e
            s = str(e).lower()
            # 429 throttle ise kısa bekle ve tekrar dene
            if "429" in s or "429" in str(getattr(e, 'code', '')):
                time.sleep(4 + deneme * 4)
                continue
            if deneme < 2:
                time.sleep(2)
                continue
            raise RuntimeError(f"Pollinations.ai görsel üretimi başarısız: {e}") from e
    else:
        if not data:
            raise RuntimeError(f"Pollinations.ai boş yanıt döndü. Son hata: {last_err}")

    # Pollinations JPEG/PNG dönebilir; tutarlı PNG'ye çevir.
    from io import BytesIO
    from PIL import Image

    try:
        im = Image.open(BytesIO(data))
        buf = BytesIO()
        im.convert("RGB").save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:  # noqa: BLE001
        return data


def _rastgele_seed() -> int:
    import random

    return random.randint(0, 2**31 - 1)


def _gorsel_prompt(baslik: str, tur_id: str, tesis: dict, sonuc: dict | None, prefs: dict) -> str:
    """Görsel üretimi için ayrıntılı, görsel-odaklı istem hazırlar (İngilizce)."""
    tesis_ad = _sanitize(tesis.get("ad", "Tesis"), 60)
    yer = _sanitize(tesis.get("il", "Turkey"), 30)

    vurgu = _sanitize(prefs.get("vurgu", "Çevre & İklim"), 40)
    tema = _sanitize(prefs.get("tema", "orman"), 20)
    stil = _sanitize(prefs.get("stil", "modern"), 40)
    notlar = _sanitize(prefs.get("notlar", ""), 300)

    ozellikler = {
        "web": "a clean professional hero image for the hotel's sustainability webpage",
        "brosur": "an elegant, natural and inviting cover image for a sustainability brochure",
        "qr": "a minimal modern and calm background for a room door / QR card",
        "basin_bulteni": "a trustworthy, corporate and bright image for a press release",
        "sosyal_medya": "an eye-catching, high-contrast, shareable image for a social media post",
        "politika": "a professional official cover image for a sustainability policy document",
        "egitim": "a warm, educational, people-focused image for staff sustainability training",
        "gorsel_afis": "a strong poster/composition image with a clear message",
        "anket_misafir": "a friendly inviting image for a guest survey cover",
        "anket_personel": "a professional neutral image for a staff survey cover",
    }

    not_metni = f" Extra guidance: {notlar}." if notlar else ""
    tema_en = {
        "orman": "green forest, natural", "okyanus": "ocean, coastal", "gün batımı": "sunset warm tones",
        "minimal": "clean minimal", "pastel": "soft pastel colors", "koyu": "dark elegant",
        "toprak": "earth tones, natural", "marka": "brand colors, modern",
    }.get(tema, tema)
    stil_en = {
        "modern": "modern", "klasik": "classic", "doğal": "natural", "lüks": "luxurious",
        "Fotorealist": "photorealistic", "Minimal / modern": "minimal modern", "İllüstrasyon": "illustration",
        "Otel markasına uyarlansın": "brand-adapted modern",
    }.get(stil, stil)

    return (
        f"Photorealistic, professional stock-style image: {ozellikler.get(tur_id, baslik + ' for the hotel')}. "
        f"Sustainable hotel '{tesis_ad}' in {yer}, Turkey. "
        f"Theme emphasis: {vurgu}. Visual theme: {tema_en}. Style: {stil_en}.{not_metni} "
        f"No text, no letters, no watermark. Natural light, high resolution, balanced composition. "
        f"Subtle realistic sustainability elements such as solar panels, green roofs and natural landscaping."
    )


# ---------------- Üretim ----------------
def uretim_olustur(
    tur_id: str,
    tesis: dict,
    sonuc: dict | None,
    prefs: dict,
) -> str:
    """İçerik türü için Gemini ile markdown çıktı üretir. RAG bağlamı kullanır."""
    tur = tur_bul(tur_id)
    if not tur:
        raise ValueError(f"Bilinmeyen içerik türü: {tur_id}")

    iskelet = ISKELETLER.get(tur_id, [])
    iskelet_md = "\n".join(f"  {i}. {b}" for i, b in enumerate(iskelet, 1))

    tercih_md = "\n".join(f"  • {k}: {v}" for k, v in prefs.items() if v not in ("", None))

    hedef_odak = _hedef_odak(tur_id, prefs)

    tesis_md = _tesis_ozeti(tesis, sonuc)

    rag = _rag_filtreli(
        f"{tur['baslik']} {prefs.get('amac','')} {prefs.get('vurgu','')}",
        TUR_RAG_FILTRE.get(tur_id, []),
        k=5,
    )
    if rag:
        rag_md = "\n\n---\n\n".join(
            f"[{r['kaynak']}]\n{r['metin']}" for r in rag
        )
    else:
        rag_md = "(KB yok veya boş; şablon bilgisi RAG'sız kullanılacak.)"

    prompt = f"""Sen KarbonAT'ın içerik üreticisisin; Türkiye'de GSTC/TGA uyumlu çalışan bir otelin sürdürülebilirlik içeriklerini yazıyorsun.

GÖREV: "{tur['baslik']}" türünde markdown içerik üret.

TÜR SINIRI (yalnız buna uy, ekstra konu açma):
{TUR_GOREV.get(tur_id, 'Yalnız bu türün içeriği.')}

İÇERİK TÜRÜ AÇIKLAMASI:
{tur.get('aciklama','')}

TESİS VERİSİ (somut rakamları AYNEN kullan, uydurma):
{tesis_md}

İSTENEN YAPI (iskelet; her maddeyi doldur, alt başlıklarla markdown olarak):
{iskelet_md}

TASARIM TERCİHLERİ (bunlara uy):
{tercih_md}

HEDEF ODAK (seçimlerin — bunlar KATI talimat, genel sürdürülebilirlik yazma):
{hedef_odak}

REFERANS ŞABLONLAR (RAG; TGA'nın gerçek şablon/politika dili — bu dilden ve maddelerden ilham al, birebir kopyalama):
{rag_md}

KURALLAR:
- Yalnız markdown çıktı, giriş cümlesi yok.
- KESİNLİKLE talimat, yönerge, prompt, 'nasıl yapılır' açıklaması VEYA tasarım/kompozisyon tarifi yazma. Çıktı yalnızca ürünün üzerinde/basılacak halinde GÖRÜNECEK SON HAZIR METİN olmalı.
- Bölüm/alan başlıklarını markdown başlığı olarak yaz (### Başlık) — tasarım motoru bunları görselde başlık olarak kullanır.
- TESİS VERİSİ'ndeki gerçek rakamları (toplam emisyon, scope, oda-gün, m², müşteri başına) çıktıda KULLAN; '0 emisyon', 'sıfır karbon' veya varsayımsal/tahmini sayı ÜRETME.
- Rakipleri/hukuk dili/yanlış iddia (green-claim) kullanma; somut veri yoksa genel ve temkinli yaz.
- Türkçe (dil tercihi farklıysa ona uy).
- İçerik uzunluğu: {prefs.get('uzunluk','Orta')}.
- Ton: {prefs.get('ton','Kurumsal & Resmi')}. Hedef kitle: {prefs.get('hedef_kitle','Misafir')}.
- Ek kullanıcı notu: {prefs.get('notlar','(yok)')}
"""

    return _gemini_cagir(prompt)


def oner_rapor(sablon: dict, tesis: dict, sonuc: dict | None, prefs: dict | None = None) -> str:
    """Rapor şablonu için Gemini ile markdown üretir. RAG yalnız bu şablonun kaynağından beslenir."""
    prefs = prefs or {}
    tesis_md = _tesis_ozeti(tesis, sonuc)
    terimler = sablon.get("kaynak", [])
    rag = _rag_filtreli(sablon["baslik"], terimler, k=5)
    if rag:
        rag_md = "\n\n---\n\n".join(f"[{r['kaynak']}]\n{r['metin']}" for r in rag)
    else:
        rag_md = "(Şablon referansı KB'de bulunamadı; formata genel TGA bilgisiyle uy.)"

    prompt = f"""Sen KarbonAT'ın rapor üreticisisin; Türkiye GSTC/TGA uyumlu otellerin resmî sürdürülebilirlik raporlama belgelerini hazırlıyorsun.

GÖREV: "{sablon['baslik']}" belgesini tesis verisine göre AYNI FORMATTA doldur.
SINIR: Yalnız bu şablonun içeriği; başka şablonun formatına kayma/suneler açma.

ŞABLON AÇIKLAMASI:
{sablon.get('aciklama','')}

TESİS VERİSİ (somut rakamları AYNEN kullan):
{tesis_md}

REFERANS ŞABLON (RAG — format/kolon/taahhüt dili buradan; birebir kopyalama):
{rag_md}

ÜRETİM BİÇİMİ:
- Yalnız markdown çıktı, giriş cümlesi yok.
- Şablonun gerçek sütun/bölüm başlıklarını kullan (Tablo X kolon adları vb.).
- Veri yoksa hücreyi "-" bırak ya da temkinli öner; uydurma rakam YAZMA.
- Türkçe; ton {prefs.get('ton','Kurumsal & Resmi')}; uzunluk {prefs.get('uzunluk','Detaylı')}.
"""
    return _gemini_cagir(prompt)


def varsayilan_prefs():
    return {
        "amac": "Bilgilendirme", "hedef_kitle": "Misafir", "ton": "Kurumsal & Resmi",
        "dil": "Türkçe", "vurgu": "Çevre & İklim", "uzunluk": "Orta",
        "tema": "orman", "notlar": "",
    }


if __name__ == "__main__":
    import argparse

    try:
        sys.stdout.reconfigure(encoding="utf-8")  # noqa: SIM115 — konsol Türkçe/emoji güvenliği
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="KarbonAT AI katmanı testi")
    ap.add_argument("--soru", help="RAG sorgu testi")
    ap.add_argument("--uretim", help="İçerik türü üretim testi (örn. rapor)")
    args = ap.parse_args()

    if args.soru:
        sonuclar = rag_sorgu(args.soru, k=4)
        print(f"{len(sonuclar)} sonuç:")
        for r in sonuclar:
            print(f"\n[{r['kaynak']} | {r['benzerlik']}]")
            print(r["metin"][:220])
    elif args.uretim:
        ornek_tesis = {
            "ad": "Örnek Tatil Köyü", "il": "Antalya", "m2": 18000,
            "oda": 220, "personel": 180, "musteri": 1200, "dolu_oda_gun": 48000,
        }
        ornek_sonuc = {
            "metrikler": {
                "toplam_ton": 1240.5, "scope1_kg": 420000, "scope2_kg": 780000,
                "scope3_kg": 40500, "oda_gun_kg": 25.8, "m2_aylik_kg": 68.9,
                "musteri_kg": 1033.75,
            },
            "statik": {"atik_bertaraf": "Düzenli depolama", "yenilenebilir": 32},
            "en_agir": {"elektrik": 45, "doğalgaz": 30},
        }
        print(uretim_olustur(args.uretim, ornek_tesis, ornek_sonuc, varsayilan_prefs()))
    else:
        ap.print_help()
