"""utils/cache.py — Two-level cache (memory + disk)"""
import json, time, hashlib
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
_mem: dict = {}

def _key(ns: str, p: dict) -> str:
    return hashlib.md5((ns + json.dumps(p, sort_keys=True)).encode()).hexdigest()

def get(ns: str, p: dict) -> Optional[Any]:
    k = _key(ns, p)
    if k in _mem:
        val, exp = _mem[k]
        if time.time() < exp: return val
        del _mem[k]
    fpath = CACHE_DIR / f"{k}.json"
    if fpath.exists():
        try:
            d = json.loads(fpath.read_text())
            if time.time() < d["exp"]:
                _mem[k] = (d["val"], d["exp"])
                return d["val"]
            fpath.unlink(missing_ok=True)
        except Exception:
            fpath.unlink(missing_ok=True)
    return None

def set(ns: str, p: dict, value: Any, ttl: int = 600):
    k = _key(ns, p); exp = time.time() + ttl
    _mem[k] = (value, exp)
    (CACHE_DIR / f"{k}.json").write_text(json.dumps({"val": value, "exp": exp}, default=str))
