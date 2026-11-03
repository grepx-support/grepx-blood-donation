# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import os
from dotenv import load_dotenv
from grepx_config.deployment import org_name
from grepx_common.phone import rules as phone_rules

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))

def _db_url(url):
    """Relative SQLite paths are resolved against the project folder, so the app works from any directory."""
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////") and not os.path.isabs(url[10:]):
        return "sqlite:///" + os.path.join(HERE, url[10:])
    return url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "change-me-in-production"
    # One setting picks the database: SQLite (default), PostgreSQL or MySQL.
    #   postgresql+psycopg://user:pass@localhost/bloodcamp   ·   mysql+pymysql://user:pass@localhost/bloodcamp
    # ---- Database: ONE line picks the engine; the rest tune connections (defaults are fine) ----------------
    DATABASE_URL = _db_url(os.getenv("DATABASE_URL", "sqlite:///instance/camp.db"))
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))           # open connections kept ready (PostgreSQL / MySQL)
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))    # extra connections allowed at busy moments
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # seconds; renew connections before servers drop them
    DB_ECHO = os.getenv("DB_ECHO", "0") == "1"                   # 1 = print every SQL statement (debugging)
    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "1") == "1"         # 0 = only ./run.sh migrate changes the schema
    ORG_NAME = org_name() or "LifeFlow Blood Camp"
    COMPANY_NAME = "GrepX Private Limited"
    COMPANY_URL = "http://grepx.sg/"
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "6591234567")  # country code, no +
    COUNTRY_CODE = phone_rules().country   # deployment file phone:
    URGENT_GROUPS = ["O-", "B-", "A-"]
    SMTP_HOST = os.getenv("SMTP_HOST", "")  # empty = emails print to console
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")  # e.g. "LifeFlow Blood Camp <hello@grepx.sg>"; empty = SMTP_USER
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")          # Sign in with Google (or set on the Integrations page)
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    TWILIO_SID = os.getenv("TWILIO_SID", "")          # empty = SMS/WhatsApp print to console
    TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
    TWILIO_SMS_FROM = os.getenv("TWILIO_SMS_FROM", "")
    TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")  # e.g. +14155238886 (sandbox)
    SITE_URL = os.getenv("SITE_URL", "")  # public address for links, e.g. https://blood.grepx.sg (empty = the address the site was opened with)
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "1") == "1"
    DONATION_GAP_DAYS = int(os.getenv("DONATION_GAP_DAYS", "90"))   # same setting donation-service uses
    WTF_CSRF_TIME_LIMIT = None
    STAFF_IDLE_MINUTES = int(os.getenv("STAFF_IDLE_MINUTES", "30"))     # admins/volunteers are logged out after this idle time
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"  # set to 1 once the site runs on https
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    # Backups: every table exported to JSON, committed and pushed to a PRIVATE GitHub repo
    BACKUP_DIR = os.path.normpath(os.path.join(HERE, os.getenv("BACKUP_DIR", "../bloodcamp-backup")))
    BACKUP_GIT_REMOTE = os.getenv("BACKUP_GIT_REMOTE", "")   # e.g. git@github.com:your-org/bloodcamp-backup.git
    BACKUP_BRANCH = os.getenv("BACKUP_BRANCH", "main")
    BACKUP_HOUR = int(os.getenv("BACKUP_HOUR", "2"))          # daily automatic backup time (needs BACKUP_GIT_REMOTE)
    # Uploaded pictures (drive banners). Kept outside git; copied into every backup under media/.
    UPLOAD_DIR = os.path.normpath(os.path.join(HERE, os.getenv("UPLOAD_DIR", "instance/uploads")))
    DRIVE_IMAGE_LIMIT = int(os.getenv("DRIVE_IMAGE_LIMIT", "3"))
    # Central picture store (see media/__init__.py). local = UPLOAD_DIR on this server; s3 = any S3-compatible bucket.
    MEDIA_STORAGE = os.getenv("MEDIA_STORAGE", "local")
    # Social media (Meta Graph API): a Facebook Page, and optionally the Instagram professional account linked to it
    META_PAGE_ID = os.getenv("META_PAGE_ID", "")
    META_PAGE_TOKEN = os.getenv("META_PAGE_TOKEN", "")       # long-lived Page access token
    META_IG_USER_ID = os.getenv("META_IG_USER_ID", "")
    META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0")
    LINKEDIN_ORG_ID = os.getenv("LINKEDIN_ORG_ID", "")      # the number in linkedin.com/company/<id>/admin
    LINKEDIN_TOKEN = os.getenv("LINKEDIN_TOKEN", "")        # access token with w_organization_social
    LINKEDIN_VERSION = os.getenv("LINKEDIN_VERSION", "202608")  # LinkedIn API version (YYYYMM); bump when LinkedIn retires it
    X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")        # X (Twitter) OAuth 2.0 user token with tweet.write
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")    # @yourchannel or a numeric chat id
    MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "")   # optional: serve pictures from a CDN/other server holding the same keys
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")  # empty for AWS; e.g. https://<account>.r2.cloudflarestorage.com
    S3_REGION = os.getenv("S3_REGION", "")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
    S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", "")      # public bucket URL; empty = short-lived signed links
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024        # whole request (3 photos straight from a phone fit easily)
