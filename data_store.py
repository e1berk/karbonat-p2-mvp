# ============================================
# KarbonAT - Veri Katmanı (Kalıcı JSON Saklama)
# Tesisler + Aylık Kayıtlar
# ============================================

import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "karbonat_db.json")

DEFAULT_DB = {"tesisler": [], "kayitlar": {}}


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


def _yeni_id():
    return "tesis_" + uuid.uuid4().hex[:10]


# ---------------- TESİSLER ----------------

def list_facilities():
    db = _db()
    return sorted(db.get("tesisler", []), key=lambda t: t.get("ad", "").lower())


def get_facility(fac_id):
    db = _db()
    for t in db.get("tesisler", []):
        if t["id"] == fac_id:
            return t
    return None


def save_facility(tesis):
    """Tesis ekler veya günceller. Dönen: kayıtlı tesis dict."""
    db = _db()
    t = dict(tesis)
    if not t.get("id"):
        t["id"] = _yeni_id()
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
