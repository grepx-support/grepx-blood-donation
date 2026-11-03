# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Forgotten passwords: a signed, one-time link (valid 1 hour) emailed to the account's address.

The token carries the user id plus a fingerprint of the current password hash, so it stops working
the moment the password changes (one use only). Nothing is stored in the database."""
import hashlib
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

class ResetError(ValueError): pass

class PasswordReset:
    MAX_AGE = 3600
    def __init__(self, secret, donors): self.s, self.donors = URLSafeTimedSerializer(secret, salt="password-reset"), donors

    @staticmethod
    def _fp(row): return hashlib.sha256((row["password_hash"] or "").encode()).hexdigest()[:16]

    def token_for(self, row): return self.s.dumps({"u": row["id"], "f": self._fp(row)})

    def user_for(self, token):
        try: data = self.s.loads(token, max_age=self.MAX_AGE)
        except SignatureExpired: raise ResetError("That link has expired (links work for 1 hour). Ask for a new one.")
        except BadSignature: raise ResetError("That link isn't valid. Ask for a new one.")
        row = self.donors.by_id(data.get("u"))
        if not row or self._fp(row) != data.get("f"): raise ResetError("That link was already used. Ask for a new one if you still need it.")
        return row
