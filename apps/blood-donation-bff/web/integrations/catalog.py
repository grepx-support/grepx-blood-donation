# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""What can be connected, which fields each needs, and how to check the connection (declarative: add an entry)."""
import grepx_contracts as gc
from dataclasses import dataclass, field
from .settings import setting

@dataclass(frozen=True)
class Field:
    key: str
    label: str
    secret: bool = False
    help: str = ""
    placeholder: str = ""

@dataclass(frozen=True)
class Integration:
    key: str
    label: str
    icon: str
    group: str
    fields: tuple
    docs: str = ""
    steps: tuple = ()
    required: tuple = field(default=())

    @property
    def setup_hint(self): return f"Integrations → {self.label}"

    def configured(self): return all(setting(k) for k in (self.required or tuple(f.key for f in self.fields if not f.key.endswith("VERSION"))))

# Connection tests run in the service that uses the account (it holds the client code): (request table, service, fields).
TESTS = {**{k: (gc.campaign.REQUESTS, gc.campaign.SERVICE, {"action": "TEST_SOCIAL", "network": k})
            for k in ("facebook", "instagram", "linkedin", "x", "telegram")},
         "email": (gc.notification.REQUESTS, gc.notification.SERVICE, {"action": "TEST_CHANNEL", "channel": "email"}),
         "twilio": (gc.notification.REQUESTS, gc.notification.SERVICE, {"action": "TEST_CHANNEL", "channel": "sms"})}

CATALOG = [
    Integration("facebook", "Facebook Page", "thumbs-up", "Social media", (
        Field("META_PAGE_ID", "Page ID", help="Facebook Page → About → Page transparency, or Meta Business Suite → Settings."),
        Field("META_PAGE_TOKEN", "Page access token", True, "Long-lived Page token with pages_manage_posts and pages_read_engagement."),
        Field("META_GRAPH_VERSION", "Graph API version", placeholder="v25.0")),
        "https://developers.facebook.com/apps",
        ("Create an app (type Business) at developers.facebook.com", "Add Facebook Login, then in Graph API Explorer pick your Page and the permissions",
         "Exchange it for a long-lived Page token and paste it here")),
    Integration("instagram", "Instagram", "camera", "Social media", (
        Field("META_IG_USER_ID", "Instagram account ID", help="Your Instagram professional account linked to the Facebook Page."),),
        "https://developers.facebook.com/docs/instagram-platform/content-publishing",
        ("Switch Instagram to a Business or Creator account and link it to the Facebook Page",
         "Uses the Facebook Page token above (add instagram_basic and instagram_content_publish)"),
        required=("META_IG_USER_ID", "META_PAGE_TOKEN")),
    Integration("linkedin", "LinkedIn page", "briefcase-business", "Social media", (
        Field("LINKEDIN_ORG_ID", "Organization ID", help="The number in linkedin.com/company/<id>/admin."),
        Field("LINKEDIN_TOKEN", "Access token", True, "Token with w_organization_social (app needs the Community Management API)."),
        Field("LINKEDIN_VERSION", "API version", placeholder="202608", help="YYYYMM; change if LinkedIn retires it.")),
        "https://www.linkedin.com/developers/apps",
        ("Create an app at linkedin.com/developers and verify it with your company page",
         "Request the Community Management API product", "Generate a token with w_organization_social and paste it here")),
    Integration("x", "X (Twitter)", "at-sign", "Social media", (
        Field("X_ACCESS_TOKEN", "OAuth 2.0 user access token", True, "From the X developer portal, with tweet.write."),),
        "https://developer.x.com/en/portal/dashboard", ("Create a project and app in the X developer portal", "Generate a user access token with tweet.write")),
    Integration("telegram", "Telegram channel", "send", "Social media", (
        Field("TELEGRAM_BOT_TOKEN", "Bot token", True, "From @BotFather in Telegram."),
        Field("TELEGRAM_CHAT_ID", "Channel", placeholder="@yourchannel")),
        "https://core.telegram.org/bots#how-do-i-create-a-bot", ("Message @BotFather, send /newbot and copy the token", "Add the bot as an admin of your channel")),
    Integration("google", "Sign in with Google", "log-in", "Sign-in", (
        Field("GOOGLE_CLIENT_ID", "Client ID", placeholder="1234…apps.googleusercontent.com"),
        Field("GOOGLE_CLIENT_SECRET", "Client secret", True, "Google Cloud → APIs & Services → Credentials → your OAuth client.")),
        "https://console.cloud.google.com/apis/credentials",
        ("Google Cloud console → APIs & Services → OAuth consent screen: type External, add your site name and email",
         "Credentials → Create credentials → OAuth client ID → Web application",
         "Authorized redirect URI: your site address + /login/google/callback (must be a domain with https, not an IP address)",
         "Copy the client ID and secret here; the Google button appears on the login and sign-up pages")),
    Integration("email", "Email (SMTP)", "mail", "Messages to people", (
        Field("SMTP_HOST", "Server", placeholder="smtp.gmail.com"), Field("SMTP_PORT", "Port", placeholder="587"),
        Field("SMTP_USER", "Username", placeholder="you@gmail.com"),
        Field("SMTP_PASS", "Password", True, "Gmail: a 16-letter App password (Google Account → Security → App passwords)."),
        Field("SMTP_FROM", "Send as", placeholder="LifeFlow Blood Camp <you@gmail.com>")),
        "https://myaccount.google.com/apppasswords", required=("SMTP_HOST", "SMTP_USER", "SMTP_PASS")),
    Integration("twilio", "SMS & WhatsApp (Twilio)", "message-circle", "Messages to people", (
        Field("TWILIO_SID", "Account SID"), Field("TWILIO_TOKEN", "Auth token", True),
        Field("TWILIO_SMS_FROM", "SMS from number", placeholder="+1…"),
        Field("TWILIO_WHATSAPP_FROM", "WhatsApp from number", placeholder="+14155238886 (sandbox)")),
        "https://console.twilio.com", ("Sign up at twilio.com and copy the Account SID and Auth token",
                                       "WhatsApp: test with the sandbox number, later register your own sender"),
        required=("TWILIO_SID", "TWILIO_TOKEN")),
]
BY_KEY = {i.key: i for i in CATALOG}
SECRET_KEYS = {f.key for i in CATALOG for f in i.fields if f.secret}
SOCIAL = {i.key: i for i in CATALOG if i.group == "Social media"}  # networks campaign-service can publish to (it does the posting)
