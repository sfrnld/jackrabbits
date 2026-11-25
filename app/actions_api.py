from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .actions import generate
from .analytics_api import _df
from .data_api import S

router = APIRouter(prefix="/api")

@router.get("/session")
def session():
    return {"loaded": "raw" in S, "confirmed": "canon" in S,
            **({"source": S["source"], "name": S["name"], "rows": len(S["canon"] if "canon" in S else S["raw"])} if "raw" in S else {})}

@router.get("/actions")
def get_actions():
    df = _df()
    if "actions" not in S: S["actions"] = generate(df)
    return {"items": S["actions"]}

class Items(BaseModel):
    items: list[dict]

@router.put("/actions")
def put_actions(b: Items):
    _df(); S["actions"] = b.items; return {"items": S["actions"]}

@router.post("/actions/regenerate")
def regen():
    S["actions"] = generate(_df()); return {"items": S["actions"]}
