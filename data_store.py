# ============================================
# KarbonAT - Veri Katmanı (Kalıcı JSON Saklama)
# Kullanıcılar + Tesisler + Aylık Kayıtlar
# ============================================

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "karbonat_db.json")

DEFAULT_DB = {"kullanicilar": [], "tesisler": [], "kayitlar": {}, "icerik_tercihleri": {}}

_SALT = "karbonat_p2_salt"


def _db():
    if not os.path.exists(DB_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        _save(DEFAULT_DB)
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(db):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _yeni_id(prefix="tesis_"):
    return prefix + uuid.uuid4().hex[:10]


# ---------------- KULLANICILAR ----------------

def _hash_sifre(sifre):
    return hashlib.sha256((_SALT + sifre).encode("utf-8")).hexdigest()


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
    """Kullanıcı adı + şifre doğrular. Başarılıysa user dict döner."""
    user = get_user_by_username(username)
    if not user:
        return None
    if hmac.compare_digest(user.get("pw_hash", ""), _hash_sifre(password)):
        return user
    return None


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
