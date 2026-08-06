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
# Not: "gemini-2.5-flash" genel takma adı yeni kullanıcılara kapalıdır (404),
# bu yüzden liste sürümlü/kararlı adlardan oluşur.
GEN_MODELS = [
    os.environ.get("GEMINI_MODEL", ""),
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gemini-2.5-pro",
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


# ---------------- Tesis özeti (prompt için) ----------------
def _tesis_ozeti(tesis: dict, sonuc: dict | None) -> str:
    if not sonuc:
        return (
            f"Tesis: {tesis.get('ad','')} · {tesis.get('m2','?')} m² · "
            f"{tesis.get('oda','?')} oda · {tesis.get('personel','?')} personel"
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
    "sosyal_medya": "Yalnız paylaşılabilecek HAZIR gönderi metinleri üret; her platform (Instagram/LinkedIn/X) için ayrı ### bölümü: gönderi metni + hashtagler + görsel alt yazısı. 'şöyle yapın' anlatımı YASAK.",
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

REFERANS ŞABLONLAR (RAG; TGA'nın gerçek şablon/politika dili — bu dilden ve maddelerden ilham al, birebir kopyalama):
{rag_md}

KURALLAR:
- Yalnız markdown çıktı, giriş cümlesi yok.
- KESİNLİKLE talimat, yönerge, prompt, 'nasıl yapılır' açıklaması VEYA tasarım/kompozisyon tarifi yazma. Çıktı yalnızca ürünün üzerinde/basılacak halinde GÖRÜNECEK SON HAZIR METİN olmalı.
- Bölüm/alan başlıklarını markdown başlığı olarak yaz (### Başlık) — tasarım motoru bunları görselde başlık olarak kullanır.
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
