# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Where the bytes live (Strategy). Keys look like 'avatar/3f/3f9c…e1.webp' and are the same on every backend."""
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

class Storage(ABC):
    @abstractmethod
    def put(self, key, data, content_type): ...
    @abstractmethod
    def delete(self, key): ...
    @abstractmethod
    def get(self, key): ...                  # bytes, or None when missing
    def path(self, key): return None          # local file, if there is one
    def public_url(self, key): return None    # direct URL, if the backend serves files itself

class LocalStorage(Storage):
    def __init__(self, root): self.root = Path(root)
    def _p(self, key):
        p = (self.root / key).resolve()
        if self.root.resolve() not in p.parents: raise ValueError("bad media key")
        return p
    def put(self, key, data, content_type):
        p = self._p(key); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    def delete(self, key):
        p = self._p(key)
        if p.is_file(): p.unlink()
    def path(self, key):
        p = self._p(key); return p if p.is_file() else None
    def get(self, key):
        p = self.path(key); return p.read_bytes() if p else None
    def move_in(self, src, key):
        p = self._p(key); p.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), p)

class S3Storage(Storage):
    """Any S3-compatible bucket. Needs `pip install boto3` (setup.sh installs it when MEDIA_STORAGE=s3)."""
    def __init__(self, cfg):
        import boto3
        self.bucket, self.base = cfg["S3_BUCKET"], (cfg.get("S3_PUBLIC_URL") or "").rstrip("/")
        self.s3 = boto3.client("s3", endpoint_url=cfg.get("S3_ENDPOINT_URL") or None, region_name=cfg.get("S3_REGION") or None,
                               aws_access_key_id=cfg.get("S3_ACCESS_KEY") or None, aws_secret_access_key=cfg.get("S3_SECRET_KEY") or None)
    def put(self, key, data, content_type):
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type, CacheControl="public, max-age=31536000, immutable")
    def delete(self, key): self.s3.delete_object(Bucket=self.bucket, Key=key)
    def get(self, key):
        try: return self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except self.s3.exceptions.NoSuchKey: return None
    def public_url(self, key):
        if self.base: return f"{self.base}/{key}"
        return self.s3.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=3600)

def storage_from(cfg):
    return S3Storage(cfg) if cfg.get("MEDIA_STORAGE", "local") == "s3" else LocalStorage(cfg["UPLOAD_DIR"])
