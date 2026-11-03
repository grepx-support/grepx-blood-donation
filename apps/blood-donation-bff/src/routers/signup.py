# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Blood-donation sign-up: a saga — donor profile (donor-service) then login credentials (auth-service)."""
import grepx_contracts as gc
from typing import Optional

from fastapi import APIRouter, Depends
from grepx_service import Saga, SagaRunner, Step
from pydantic import BaseModel

from grepx_bff.errors import ApiError
from grepx_bff.gateway import CURRENT_TRACE
from grepx_bff.routers.auth import session
from grepx_bff.security import gateway

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUp(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    blood_group: str = ""
    sex: str = ""
    weight: Optional[float] = None
    dob: str = ""
    invite_code: str = ""


@router.post("/register")
def register(body: SignUp, gw=Depends(gateway)):
    sealed = gw.box.seal(body.password)
    if len(body.password) < 8:
        raise ApiError("WEAK_PASSWORD", 400)
    saga = Saga("donor-sign-up", [
        Step("person", gc.people.REQUESTS, gc.people.SERVICE,
             lambda s: {"action": "CREATE", **body.model_dump(exclude={"password"}, exclude_none=True), "link": f"{gw.site}/dashboard"}),
        Step("login", gc.auth.REQUESTS, gc.auth.SERVICE,
             lambda s: {"action": "REGISTER", "user_id": s["person"]["person_id"], "email": body.email, "password_enc": sealed}),
    ])
    outcome = SagaRunner(gw.requests).run(saga, {}, trace_id=CURRENT_TRACE.get() or None)
    if not outcome.ok:
        raise ApiError(outcome.reason)
    return session(gw, gw.command(gc.auth.REQUESTS, gc.auth.SERVICE, {"action": "LOGIN", "email": body.email, "password_enc": sealed}))


