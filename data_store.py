# ============================================
# KarbonAT - Veri Katmanı (Kalıcı JSON Saklama)
# Kullanıcılar + Tesisler + Aylık Kayıtlar
# ============================================

import bcrypt
import json
import os
import tempfile
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "karbonat_db.json")

DEFAULT_DB = {"kullanicilar": [], "tesisler": [], "kayitlar": {}, "icerik_tercihleri": {}, "raporlar": {}}


def _db():
    if not os.path.exists(DB_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        _save(DEFAULT_DB)
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(db):
    """Atomik yazma: temp dosya → rename (crash'ta yarım yazma engellenir)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DB_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _hash_sifre(sifre):
    """bcrypt ile şifre hash'leme."""
    return bcrypt.hashpw(sifre.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_sifre(sifre, pw_hash):
    """bcrypt + eski SHA256 uyumlu doğrulama (geriye dönük)."""
    if not pw_hash:
        return False
    # bcrypt hash'i $2 ile başlar
    if pw_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(sifre.encode("utf-8"), pw_hash.encode("utf-8"))
        except Exception:
            return False
    # Eski tek geçiş SHA256 fallback (sabit salt)
    import hashlib
    import hmac
    eski = hashlib.sha256(("karbonat_p2_salt" + sifre).encode("utf-8")).hexdigest()
    return hmac.compare_digest(pw_hash, eski)


def _yeni_id(prefix="tesis_"):
    return prefix + uuid.uuid4().hex[:10]


# ---------------- KULLANICILAR ----------------

def list_users():
    db = _db()
    return db.get("kullanicilar", [])


def get_user_by_username(username):
    for u in list_users():
        if u["username"].lower() == username.strip().lower():
            return u
    return None


def get_user_by_id(user_id):
    for u in list_users():
        if u["id"] == user_id:
            return u
    return None


def create_user(username, password, fullname=""):
    """Yeni kullanıcı oluşturur. Başarısızsa None döner."""
    username = username.strip()
    if not username or not password:
        return None
    if get_user_by_username(username):
        return None
    db = _db()
    user = {
        "id": _yeni_id("user_"),
        "username": username,
        "fullname": fullname.strip() or username,
        "pw_hash": _hash_sifre(password),
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    db.setdefault("kullanicilar", []).append(user)
    _save(db)
    return user


def verify_login(username, password):
    """Kullanıcı adı + şifre doğrular. Başarılıysa user dict döner. Eski hash'i otomatik bcrypt'e geçirir."""
    user = get_user_by_username(username)
    if not user:
        return None
    pw_hash = user.get("pw_hash", "")
    if not _verify_sifre(password, pw_hash):
        return None
    # Eski SHA256 ise bcrypt'e yükselt
    if not pw_hash.startswith("$2"):
        try:
            db = _db()
            for u in db.get("kullanicilar", []):
                if u["id"] == user["id"]:
                    u["pw_hash"] = _hash_sifre(password)
                    break
            _save(db)
            user["pw_hash"] = db.get("kullanicilar", [])[-1]["pw_hash"] if db.get("kullanicilar") else _hash_sifre(password)
        except Exception:
            pass
    return user


# ---------------- TESİSLER ----------------

def list_facilities(owner_id=None):
    db = _db()
    tes = db.get("tesisler", [])
    if owner_id:
        tes = [t for t in tes if t.get("owner") == owner_id]
    return sorted(tes, key=lambda t: t.get("ad", "").lower())


def count_facilities(owner_id=None):
    return len(list_facilities(owner_id))


def get_facility(fac_id):
    db = _db()
    for t in db.get("tesisler", []):
        if t["id"] == fac_id:
            return t
    return None


def save_facility(tesis, owner_id=None):
    """Tesis ekler veya günceller. Dönen: kayıtlı tesis dict."""
    db = _db()
    t = dict(tesis)
    if not t.get("id"):
        t["id"] = _yeni_id()
    if owner_id and not t.get("owner"):
        t["owner"] = owner_id
    t["updated"] = datetime.now().isoformat(timespec="seconds")
    if not t.get("created"):
        t["created"] = t["updated"]

    listed = db.setdefault("tesisler", [])
    for i, mevcut in enumerate(listed):
        if mevcut["id"] == t["id"]:
            listed[i] = t
            break
    else:
        listed.append(t)
    _save(db)
    return t


def delete_facility(fac_id):
    db = _db()
    db["tesisler"] = [t for t in db.get("tesisler", []) if t["id"] != fac_id]
    db.get("kayitlar", {}).pop(fac_id, None)
    db.get("icerik_tercihleri", {}).pop(fac_id, None)
    db.get("raporlar", {}).pop(fac_id, None)
    _save(db)


# ---------------- AYLIK KAYITLAR ----------------

def list_records(fac_id):
    """Belirli tesisin tüm aylık kayıtlarını döner (kronolojik)."""
    db = _db()
    kayitlar = db.get("kayitlar", {}).get(fac_id, [])
    return sorted(kayitlar, key=lambda r: r.get("period", ""))


def get_record(fac_id, period):
    for r in list_records(fac_id):
        if r.get("period") == period:
            return r
    return None


def get_previous_record(fac_id, period):
    """Verilen dönemden önceki en yakın kaydı döner (karşılaştırma için)."""
    oncekiler = [r for r in list_records(fac_id) if r.get("period", "") < period]
    if oncekiler:
        return oncekiler[-1]
    return None


def save_record(record):
    """Aylık kayıt ekler veya aynı dönem varsa üzerine yazar."""
    db = _db()
    fac_id = record.get("fac_id")
    period = record.get("period")
    kayitlar = db.setdefault("kayitlar", {}).setdefault(fac_id, [])
    r = dict(record)
    r["created"] = datetime.now().isoformat(timespec="seconds")

    for i, mevcut in enumerate(kayitlar):
        if mevcut.get("period") == period:
            kayitlar[i] = r
            break
    else:
        kayitlar.append(r)
    _save(db)
    return r


def delete_record(fac_id, period):
    db = _db()
    kayitlar = db.get("kayitlar", {}).get(fac_id, [])
    db["kayitlar"][fac_id] = [r for r in kayitlar if r.get("period") != period]
    _save(db)


# ---------------- İÇERİK TERCİHLERİ ----------------

def get_content_prefs(fac_id, tur_id):
    """Tesis + içerik türü için kayıtlı tercihleri döner (yoksa None)."""
    db = _db()
    return db.get("icerik_tercihleri", {}).get(fac_id, {}).get(tur_id)


def save_content_prefs(fac_id, tur_id, prefs):
    """İçerik türü tercihlerini kaydeder/üzerine yazar."""
    db = _db()
    d = db.setdefault("icerik_tercihleri", {}).setdefault(fac_id, {})
    p = dict(prefs)
    p["updated"] = datetime.now().isoformat(timespec="seconds")
    d[tur_id] = p
    _save(db)
    return p


# ---------------- RAPORLAR (dönem bazlı, profil→rapor→aylar) ----------------

def list_report_periods(fac_id):
    """Bu tesise ait en az bir AI/deterministik rapor kaydı olan dönemleri döner."""
    db = _db()
    return sorted(db.get("raporlar", {}).get(fac_id, {}).keys(), reverse=True)


def get_report(fac_id, period, sablon_id):
    """Belirli dönem + şablon için kayıtlı raporu döner (yoksa None)."""
    db = _db()
    return db.get("raporlar", {}).get(fac_id, {}).get(period, {}).get(sablon_id)


def save_report(fac_id, period, sablon_id, metin, tip="ai"):
    """Üretilen raporu kaydeder (aynı şablon/dönem varsa üzerine yazar)."""
    db = _db()
    donemler = db.setdefault("raporlar", {}).setdefault(fac_id, {})
    kayit = {
        "sablon_id": sablon_id,
        "tip": tip,
        "metin": metin,
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    donemler.setdefault(period, {})[sablon_id] = kayit
    _save(db)
    return kayit


def get_saved_reports(fac_id, period):
    """Belirli dönemdeki tüm kayıtlı raporları döner."""
    db = _db()
    return db.get("raporlar", {}).get(fac_id, {}).get(period, {})


# ---------------- MEDYA (tesis bazlı, tür başına kayıt) ----------------

def get_media(fac_id, tur_id):
    """Belirli tür için kayıtlı medya içeriğini döner (yoksa None)."""
    db = _db()
    return db.get("medya", {}).get(fac_id, {}).get(tur_id)


def save_media(fac_id, tur_id, metin, gorsel=None):
    """Üretilen/düzenlenen medya içeriğini kaydeder; önceki sürümü versions[]'a arşivler."""
    db = _db()
    medya = db.setdefault("medya", {}).setdefault(fac_id, {})
    eski = medya.get(tur_id)
    versions = []
    if eski:
        # Eski sürümü sakla (en fazla son 5)
        versions = list(eski.get("versions") or [])
        versions.append({
            "metin": eski.get("metin", ""),
            "created": eski.get("created", ""),
            "updated": eski.get("updated", ""),
            "gorsel_yol": eski.get("gorsel_yol"),
        })
        versions = versions[-5:]
    kayit = {
        "tur_id": tur_id,
        "metin": metin,
        "created": (eski or {}).get("created", datetime.now().isoformat(timespec="seconds")),
        "updated": datetime.now().isoformat(timespec="seconds"),
        "versions": versions,
    }
    # Görsel dosyasını versiyonlayarak saklamak yerine ana görseli güncelle; eski görsel dosyası korunur
    if eski and eski.get("gorsel_yol") and eski["gorsel_yol"] != _media_gorsel_yol(fac_id, tur_id):
        kayit["gorsel_yol"] = eski.get("gorsel_yol")
    if gorsel is not None:
        yol = _media_gorsel_yol(fac_id, tur_id)
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        # Önceki görseli arşivle
        if eski and eski.get("gorsel_yol") and os.path.exists(eski["gorsel_yol"]):
            try:
                import shutil
                arsiv = yol.replace(".png", f"_{kayit['updated'].replace(':','-')}.png")
                shutil.copyfile(eski["gorsel_yol"], arsiv)
            except Exception:
                pass
        with open(yol, "wb") as f:
            f.write(gorsel)
        kayit["gorsel_yol"] = yol
    elif eski and eski.get("gorsel_yol"):
        kayit["gorsel_yol"] = eski.get("gorsel_yol")
    medya[tur_id] = kayit
    _save(db)
    return kayit


def _media_gorsel_yol(fac_id, tur_id):
    return os.path.join(DATA_DIR, "images", f"{fac_id}__{tur_id}.png")
