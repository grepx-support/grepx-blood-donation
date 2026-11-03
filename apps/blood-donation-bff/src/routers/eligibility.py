"""Eligibility quick form + LifeBot chat. Public; the chat state travels with the client."""
import grepx_contracts as gc
from typing import Optional

from fastapi import APIRouter, Depends

from grepx_bff.security import gateway, optional_user

router = APIRouter(prefix="/eligibility", tags=["eligibility"])


@router.post("/check")
def check(answers: dict, gw=Depends(gateway)):
    v = gw.command(gc.questionnaire.REQUESTS, gc.questionnaire.SERVICE, {"action": "CHECK", "answers": answers})
    return {k: v.fields[k] for k in ("eligible", "reasons", "notes")}


@router.post("/chat")
def chat(body: dict, gw=Depends(gateway), user: Optional[object] = Depends(optional_user)):
    v = gw.command(gc.questionnaire.REQUESTS, gc.questionnaire.SERVICE, {"action": "CHAT", "message": body.get("message", ""), "state": body.get("state") or {}})
    return {"reply": v.fields["reply"], "state": v.fields["state"]}
