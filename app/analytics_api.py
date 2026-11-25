from __future__ import annotations
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from . import analytics as A
from .assistant import parse
from .data_api import S
from .findings_api import _state

router = APIRouter(prefix="/api")

def _df():
    if "canon" not in S: raise HTTPException(409, "Pilih data dan konfirmasi pemetaan kolom dulu")
    _state()                                  # refreshes S["clean"] from the user's current decisions
    return S["clean"]

def _log(who, text, **kw):
    S.setdefault("timeline", []).append(dict(t=time.strftime("%H:%M:%S"), who=who, text=text, **kw))

def _guard(fn, *a, **k):
    try: return fn(*a, **k)
    except ValueError as e: raise HTTPException(422, str(e))

class Q(BaseModel):
    filters: dict = Field(default_factory=dict)
    group_by: str | None = None
    metric: str = "net"
    compare: list[str] | None = None
    top: int | None = None

@router.get("/analytics/options")
def options(): return A.options(_df()) | {"metrics": A.METRICS, "drill": A.DRILL}

@router.post("/analytics/query")
def query(q: Q): return _guard(A.query, _df(), **q.model_dump())

class Drv(BaseModel):
    group_dim: str; key: str; a: str; b: str; filters: dict = Field(default_factory=dict)

@router.post("/analytics/drivers")
def drivers(b: Drv): return _guard(A.drivers, _df(), b.group_dim, b.key, b.a, b.b, b.filters)

class Scope(BaseModel):
    filters: dict = Field(default_factory=dict); n: int = 5

@router.post("/analytics/weakest")
def weakest(b: Scope): return _guard(A.weakest, _df(), b.filters, b.n)

@router.post("/analytics/insights")
def insights(b: Scope): return {"insights": _guard(A.insights, _df(), b.filters)}

class Ser(BaseModel):
    filters: dict = Field(default_factory=dict); split_by: str = "brand"; x: str = "week"; metric: str = "net"

@router.post("/analytics/series")
def series(b: Ser): return _guard(A.series, _df(), **b.model_dump())

@router.post("/analytics/outlets")
def outlets(b: Scope): return {"items": _guard(A.outlet_rows, _df(), b.filters)}

class Say(BaseModel):
    text: str; filters: dict = Field(default_factory=dict)

@router.post("/assistant")
def assistant(b: Say):
    r = parse(b.text, _df(), b.filters)
    _log("user", b.text); _log("assistant", r["message"], intent=r["intent"], filters=r["filters"])
    return r

@router.get("/timeline")
def timeline(): return {"items": S.get("timeline", [])}
