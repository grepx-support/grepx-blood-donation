<!--
  Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
  This file is part of the GrepX platform and is proprietary and confidential.
  Unauthorised copying, use, modification or distribution is strictly prohibited.
-->

# LifeFlow Blood Camp — Complete Functional & Technical Specification

> Purpose: a stack‑independent description of **everything** this website does, detailed enough to
> re‑implement it in another technology (e.g. Django, Spring Boot, .NET, Node/Next.js, Go) with the
> same behaviour. The reference implementation is Python/Flask in this repository.
>
> Owner: GrepX Private Limited, Singapore (http://grepx.sg/). Product name: **LifeFlow Blood Camp**.

---

## 0. How to use this document

1. Build the **data model** (§4) and **roles/permissions** (§3) first — everything depends on them.
2. Implement the **public site** (§6) and **auth** (§7), then the **donor area** (§8).
3. Implement the **staff workspace** (§9–§20) module by module; each section lists routes, inputs, rules and side‑effects.
4. Wire **messaging** (§21–§22), **background jobs** (§23), **integrations** (§24–§26), **media** (§27), **backup/migrations/CLI** (§28–§30).
5. Apply **security** (§31) and **UI conventions** (§32). §33 is an acceptance checklist.

Conventions: routes are written `METHOD /path`. "Staff" = volunteer or admin. Dates are ISO `YYYY-MM-DD`; times `HH:MM` 24h. Timezone default **Asia/Singapore** (env `TIMEZONE`). Country code default **65**.

---

## 1. Product overview

A website for running community **blood donation drives** in Singapore:

- **Public**: browse upcoming drives, book a time slot, show interest, check eligibility (form + chatbot "LifeBot"), self check‑in at the venue (kiosk), verify/share donation certificates, refer friends.
- **Donors**: dashboard with eligibility countdown, digital donor card with QR, impact & badges, bookings, certificates & vouchers, referral leaderboard, calendar feed, assigned tasks, profile + photo.
- **Volunteers** (granular permissions): check‑in desk, drive management, tasks/planning, donors, messages, reports.
- **Admins**: everything, incl. users & passwords, volunteer roles, integrations (social, email, SMS/WhatsApp), automatic message wording, analytics widget visibility.

One login for all three roles; the UI shows what each role may use.

---

## 2. Technology of the reference implementation (for orientation only)

| Concern | Reference | Notes for re‑implementation |
|---|---|---|
| Web | Flask app factory + blueprints, Jinja2 server‑rendered HTML | Any MVC/SSR framework; or SPA + JSON API |
| Partial updates | htmx 2 (`HX-Request`, `HX-Trigger`, `HX-Refresh`, `HX-Replace-Url` headers) | Equivalent AJAX |
| Client behaviour | Alpine.js 3, SortableJS (drag‑drop), ApexCharts, Mermaid, Swiper, Notyf (toasts), QR generator + camera scanner | |
| Styling | Tailwind 4 + DaisyUI 5, Lucide icons via pure CSS | Rose/red brand (#E11D48), light/dark theme toggle |
| DB | SQLAlchemy Core, raw SQL in repositories; SQLite default; PostgreSQL / MySQL via `DATABASE_URL` | Pool size/overflow/recycle/echo configurable |
| Auth | Flask‑Login sessions, Werkzeug password hashes | |
| CSRF | Flask‑WTF on every POST | |
| Validation | Pydantic v2 | |
| Jobs | APScheduler in‑process | Any scheduler/cron/queue |
| Excel | openpyxl | |
| Images | Pillow (WebP output) | |
| Tokens | itsdangerous (signed, time‑limited) | |
| Secrets at rest | Fernet encryption keyed by `SECRET_KEY` | |
| Messaging | SMTP, Twilio (SMS + WhatsApp) | |
| Social | Meta Graph API v25.0, LinkedIn REST Posts API, X API v2, Telegram Bot API | |
| Storage | Local disk or S3‑compatible (boto3) | |

Design patterns used (keep them; they make features pluggable): Repository (all SQL in repos), Strategy/Registry (message channels, social networks, storage backends), Facade (Messenger, MediaService), Observer (EventBus for domain events), Builder (DonorQuery), Template Method (chart widgets, Twilio channels), Policy objects (TaskPolicy, AutoPolicy), State machine (LifeBot chat flow).

---

## 3. Roles & permissions

### 3.1 Roles (column `donors.role`)
- `donor` — default for every registration.
- `volunteer` — staff with permissions from (a) a **volunteer role** (`staff_role_id` → `staff_roles.perms`) ∪ (b) **personal permissions** (`permissions` table).
- `admin` — all permissions, always.

### 3.2 Permissions
| Key | Grants |
|---|---|
| `manage_drives` | Create/edit/clone/complete drives, slots, pictures, social posting, announce |
| `checkin` | Check‑in desk, walk‑ins, QR scan, attendee status |
| `notify` | Send messages/invitations to donors |
| `manage_donors` | Donor grid, add/edit donors, bulk actions, export, segments |
| `bulk_import` | Excel import |
| `view_log` | Messages page / delivery log |
| `manage_tasks` | Planning board for all tasks, checklists |
| `reports` | Drive reports & retrospectives |

`user.can(perm)` = `role == admin` OR perm ∈ (personal perms ∪ role perms). `is_staff` = role ∈ {volunteer, admin}.

### 3.3 Default volunteer roles (seeded by migration)
| Role | Perms |
|---|---|
| Check-in desk | checkin |
| Drive coordinator | manage_drives, checkin, manage_tasks, reports |
| Donor relations | manage_donors, notify, view_log |
| Data entry | manage_donors, bulk_import |

### 3.4 Guards
- `staff_required` → 403/redirect if not volunteer/admin.
- `admin_required`.
- `permission_required(*perms)` → any of the listed perms.
- Admin‑only areas: Users & passwords, Volunteers & admins, Integrations, analytics access matrix, test message.

---

## 4. Data model

All tables have integer PK `id` unless noted. `created` timestamps default to now (UTC ISO string).

### donors (all people: donors, volunteers, admins)
`id, name, email UNIQUE, phone, password_hash, blood_group (A+,A-,B+,B-,AB+,AB-,O+,O-, or NULL = unknown), sex (Male|Female), weight REAL kg, dob DATE, role (donor|volunteer|admin), ref_code (6 hex, unique, lazily created), referred_by → donors.id, cal_token (secret for ICS feed), staff_role_id → staff_roles.id, photo_id → media.id, created`

### permissions
`donor_id, perm` (personal extra permissions)

### staff_roles
`id, name, description, perms (comma‑separated)`

### drives
`id, title, venue, drive_date DATE, time_slot TEXT (e.g. "10:00 – 17:00", free text), description, capacity INT default 100, image_url (cover; media id, legacy path or http(s) URL), images JSON array (≤3; first = cover), status (open|completed), completed_at, completed_by → donors.id`

### slots
`id, drive_id, starts_at "HH:MM", ends_at "HH:MM", capacity INT`

### interests (registrations/bookings)
`id, drive_id, donor_id (nullable for guests), name, phone, email, status (interested|confirmed|donated|no_show), slot_id, source (online|walkin|kiosk), reminded_at, created; UNIQUE(drive_id, donor_id)`
Status rank (never downgrade on merge): interested 0 < confirmed 1 < no_show 2 < donated 3.

### donations
`id, donor_id, drive_id (nullable), donated_on DATE, units default 1`

### notifications (delivery log)
`id, drive_id, channel (email|sms|whatsapp|social…), recipient, status (sent|logged|failed), event, subject, created`
`logged` = channel not configured, message printed to console only.

### import_rows
`id, batch (uuid), row_no, data JSON, errors JSON, status (valid|error|ignored|imported|skipped)`

### tasks
`id, title, description, due_at "YYYY-MM-DDTHH:MM", assignee_id, created_by, drive_id, status (todo|in_progress|blocked|done), important 0/1, remind 0/1, reminded_at, phase (Planning|Promotion|Logistics|Drive day|Follow-up|NULL), created`

### task_events (audit)
`id, task_id, by_id, action (created|assigned|status|edited|claimed|…), detail, at`

### widget_access
`widget, audience` — audience ∈ public|donor|volunteer|admin, or the sentinel `_none` meaning "explicitly nobody".

### drive_reports
`drive_id PK, stats JSON (snapshot), went_well, to_improve, actions (one per line), notes, rating 1–5, updated_by, updated_at`

### donor_segments (saved donor-grid views)
`id, name, query (querystring), created_by`

### media
`id (32 hex), kind (drive|avatar), key (storage path), content_type, size, width, height, owner_id, created`

### social_posts
`id, drive_id, network, status (posted|failed), external_id, permalink, error, caption, created_by, created`

### certificates
`id (32 hex = public verification code), donor_id, drive_id, donated_on, sent_at; UNIQUE(donor_id, drive_id)`

### vouchers
`id, drive_id, donor_id, title, partner, details, code, expires_on`

### app_settings
`name PK, value` (secrets stored as `enc:<fernet token>`)

### schema_migrations
`name PK, applied_at`

Indexes: on foreign keys, `interests(drive_id,status)`, `donations(donor_id)`, `tasks(assignee_id,status)`, `notifications(created)` etc.

---

## 5. Configuration (environment variables / `.env`)

| Key | Default | Meaning |
|---|---|---|
| SECRET_KEY | random dev | Sessions, tokens, settings encryption |
| DATABASE_URL | sqlite:///instance/bloodcamp.db | sqlite / postgresql / mysql |
| DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE, DB_ECHO | | Pooling |
| AUTO_MIGRATE | on | Run migrations on start |
| ORG_NAME | LifeFlow Blood Camp | Shown everywhere |
| COMPANY_NAME / COMPANY_URL | GrepX Private Limited / http://grepx.sg/ | Footer "Developed by" |
| WHATSAPP_NUMBER | | "Ask on WhatsApp" links (wa.me) |
| COUNTRY_CODE | 65 | Phone normalisation |
| URGENT_GROUPS | O-,B-,A- | Badges on home page |
| SITE_URL | http://localhost:5000 | Absolute links in messages/posters (warning if localhost) |
| TIMEZONE | Asia/Singapore | |
| DONATION_GAP_DAYS | 90 | Days between donations |
| STAFF_IDLE_MINUTES | 30 | Staff idle logout |
| SESSION_COOKIE_SECURE | off | HTTPS cookies |
| SCHEDULER_ENABLED | on | Background jobs |
| SMTP_HOST, SMTP_PORT (587 STARTTLS / 465 SSL), SMTP_USER, SMTP_PASS, SMTP_FROM | | Email |
| TWILIO_SID, TWILIO_TOKEN, TWILIO_SMS_FROM, TWILIO_WHATSAPP_FROM | | SMS/WhatsApp |
| UPLOAD_DIR | instance/uploads | Local media |
| DRIVE_IMAGE_LIMIT | 3 | Pictures per drive |
| MEDIA_STORAGE | local | local \| s3 |
| S3_BUCKET, S3_ENDPOINT_URL, S3_REGION, S3_ACCESS_KEY, S3_SECRET_KEY, S3_PUBLIC_URL | | S3 |
| MEDIA_BASE_URL | | Public base for media in social posts |
| META_PAGE_ID, META_PAGE_TOKEN, META_IG_USER_ID, META_GRAPH_VERSION (v25.0) | | Facebook/Instagram |
| LINKEDIN_ORG_ID, LINKEDIN_TOKEN, LINKEDIN_VERSION (202608) | | LinkedIn |
| X_ACCESS_TOKEN | | X/Twitter |
| TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID | | Telegram |
| BACKUP_DIR (../bloodcamp-backup), BACKUP_GIT_REMOTE, BACKUP_BRANCH, BACKUP_HOUR (2) | | Nightly git backup |
| MAX_CONTENT_LENGTH | 25 MB | Upload limit |

Integration settings can also be set in the **Integrations** admin page; stored values (app_settings) override `.env`.

---

## 6. Public site

### Layout (public)
Sticky header: logo (droplet) + ORG_NAME, nav (Drives `#events`, Eligibility, Impact, FAQ), theme toggle, Log in / Dashboard / Workspace (staff) / Log out. Footer: © year, company, link, "Developed by GrepX". Floating **LifeBot chat** button on all public pages (event `open-chat` opens it). Flash messages rendered as toasts. Global "Show interest" modal (event `interest` with drive id/title).

### 6.1 `GET /` Home
Sections in order:
1. **Reminder banner** (logged‑in donor): from ReminderService message, with "Find a drive".
2. **Hero**: badge "N upcoming drives in Singapore"; headline "Your blood. Someone's tomorrow."; CTA "See upcoming drives" and "Can I donate?" (opens chatbot); **Urgently needed** blood‑group badges (URGENT_GROUPS).
3. **Next drive card** with live countdown (days/hours/mins/secs), cover image, venue, fill bar, actions; or "New drives coming soon → Notify me" (register).
4. **Stats bar** (count‑up animation): Registered donors, Donations made, Lives touched (= donations × 3), Upcoming drives.
5. **Upcoming events carousel** (`#events`): each card: cover image, countdown label ("Today", "Tomorrow", "In N days"), "N going", date tile, title, venue, time, actions, "Details →". Empty state → "Get notified".
6. **Basic requirements** (`#eligibility`) — requirement cards + "Check me with LifeBot" / "Use the quick form".
7. **Live impact** (`#impact`) — analytics widgets visible to the current audience (§16).
8. **FAQ** accordion (5 Q&As: how long ~45 min/10 min donation; does it hurt; how often ~12 weeks; before donating; travel).
9. **CTA band** "Be someone's hero this month" → Become a donor / WhatsApp us.

Upcoming drive query = status open AND drive_date ≥ today, ordered by date, with counts: `going` (interests not no_show), `donated`, `slot_count`.

**Drive actions** (macro used on cards): if user booked → status badge; if drive has slots → "Book a time" (to drive page `#book`); else logged‑in → "I'm going" (POST confirm); guest → "Register" + "Interested".
**Fill bar**: going / capacity with %.

### 6.2 `GET /drive/<id>` Drive page
- Open Graph meta: title "🩸 {title} · {date}", description venue/time, image = poster `/drive/<id>/poster.jpg` (1080×1080).
- Hero image + countdown badge + date/time/venue.
- "About this drive" (description or default text). Pictures gallery (if >1) with lightbox modal.
- "Before you come": eat a meal 3 h before; drink 500 ml water; bring NRIC/ID; sleep well.
- Embedded Google Map of venue + Directions link.
- Sticky side card: date tile, fill bar; **current booking** alert ("You're confirmed for 10:00–10:30") + "Cancel my booking"; **slot picker** (3‑column grid; each shows start time and "N left"/"Full"; full slots disabled unless it is my slot) → "Book this time" (logged in) or "Sign up to book a time" (→ `/register?drive=<id>`) + "Log in"; "Not sure yet? Show interest". If no slots and not booked → generic drive actions.
- More: "At the venue? Check in here" (kiosk), "Download .ics", "Ask on WhatsApp" (prefilled text), "Google Cal" link (uses booked slot times when booked), Share (Web Share API / copy, with poster image).
- Completed drives are not bookable.

### 6.3 `GET /drive/<id>/calendar.ics`
Single VEVENT for the drive (uses booked slot times if the user has one; otherwise parses `time_slot` or all‑day).

### 6.4 `POST /drive/<id>/interest` (guest or logged in)
Fields: name, phone, email (ContactForm). Normalise phone. Adds interest with status `interested`, source `online`. Merge rules (InterestRepo.add): if the donor already has a row, keep the higher status (never downgrade); guest rows matched by email/phone are adopted when the person later registers/logs in. Flash "Thanks! We'll keep you posted". htmx → toast.

### 6.5 `POST /drive/<id>/confirm` (login required)
Optional `slot_id`. BookingService:
- Drive has slots → slot required (`SlotRequired` → flash "Pick a time"); slot full (booked ≥ capacity, counting all statuses except no_show) → `SlotFull` flash. Changing slot frees the old one.
- Sets status `confirmed` (unless already donated), source online. Flash success; redirect back to drive page.

### 6.6 `POST /drive/<id>/cancel` (login)
Deletes the user's interest for that drive (not if donated). Flash.

### 6.7 `GET|POST /eligibility` — quick form
Fields: dob (required), sex (Female/Male), weight (required), hb (optional), last donation date (optional), yes/no: illness (7 days), fever (4 weeks), advisory (overnight in India/Batam/Bintan in last 4 months) + `advisory_return` date when yes, abroad (other trips 3 months), travel (malaria/Zika area), tattoo (6 months), pregnant, medication. Nothing stored.
Result = `(eligible, reasons[], notes[])` displayed as: success alert (+confetti) "Great news — you look eligible!" → Find a drive; or warning "Not right now — but thank you!" with reasons list; info alert with notes + link to HSA eligibility checker.

**Eligibility rules** (§ constants: AGE_MIN 16, AGE_MAX 65, REPEAT_AGE_MAX 75, CONSENT_BELOW 18, WEIGHT_MIN 45, HB_MIN F 12.5 / M 13.0, SYMPTOM_FREE_DAYS 7, FEVER_FREE_WEEKS 4, ADVISORY places India/Batam/Bintan wait 4 months, gap DONATION_GAP_DAYS 90):
| Rule | Blocking message | Note (non‑blocking) |
|---|---|---|
| Age | "Donors must be at least 16." / over 65: "Repeat donors can donate up to age 75." (if repeat) else first‑time limit message | 16–17: "you'll need a signed parental consent form" |
| Weight | "You need to weigh at least 45 kg." | |
| Hemoglobin (if given) | "Haemoglobin should be at least {F12.5/M13.0} g/dL (nurses test it at the drive)." | |
| Gap | "Wait 90 days between donations." (last donation < 90 days ago) | |
| Symptoms | "Wait until you've had no sore throat, cough, runny nose or diarrhoea for at least 7 days." | |
| Fever | "No fever for 4 weeks is needed before donating." | |
| Travel advisory | "After an overnight stay in India, Batam or Bintan, please wait 4 months: you can donate from {return+4 months}." (only if still within window) | |
| Travel | "A recent trip to a malaria or Zika risk area may mean a short wait." | if travel or abroad: "Check the waiting time for each country you visited on the HSA website" |
| Tattoo | "Tattoo/piercing in the last 6 months: please wait." | |
| Pregnancy | "Pregnancy or breastfeeding: not eligible right now." | |
| Medication | "Antibiotics or blood thinners: ask the camp doctor first." | |

**Requirement cards** (`REQUIREMENTS`, shown on home & eligibility): age 16–65 (repeat to 75, consent under 18), weight ≥45 kg, healthy/feeling well, haemoglobin levels, 12 weeks between donations, travel advisory, bring ID — each with icon + short text.

### 6.8 LifeBot chatbot — `POST /api/chat` (JSON)
Request `{message}`; response `{reply, options[] (tap buttons), done?, eligible?}`. State kept in session (`chat` key). `"restart"` resets. Steps (state machine): **age** (number) → **repeat** (only if age > 65: "Have you donated before?") → **weight** → **sex** → **illness** → **fever** → **advisory** → **advisory_return** (date, only if yes) → **abroad** → **risk** (malaria/Zika) → **tattoo** → **pregnant** (only if female) → **medication** → evaluate with the same rules → final message with reasons/notes and buttons ("Find a drive", "Start again"). Invalid input re‑asks the same question with a hint. Widget: floating panel, typing indicator, quick‑reply chips.

### 6.9 `GET /join/<ref_code>` Referral link
Stores ref code in session and redirects to register (register page shows "You were invited by a friend" banner). Unknown code → just redirect.

### 6.10 Kiosk (self check‑in at venue) — `/drive/<id>/here/`
For a tablet / QR poster at the venue.
- Logged in: if my booking is confirmed/donated → "You're checked in, {first name}! Your time: 10:00. Please take a seat." else "Are you here?" → POST `/here/checkin` with `me=1`.
- **Find me**: POST `/here/find` `contact` (exact phone or email only, privacy). Found → show first name + last initial, masked phone (e.g. `+65 ••••1234`), blood group, avatar; stored in session `kiosk_found` → "Check in" posts to `/here/checkin`. Not found → flash "Not found — register below".
- **New here**: POST `/here/new` quick‑register (name, phone, email optional, blood group, sex) → creates donor via WalkInService and checks in (source `kiosk`).
- Check‑in sets status `confirmed` (never downgrades donated). Completed drive → refuse.

### 6.11 Certificates (public)
- `GET /certificate/<code>` page: "Certificate of appreciation", donor name, "Verified · issued by ORG · date", Download PNG, Print/PDF, Share (prefilled text with hashtags #BloodDonation #SaveLives), certificate number = first 8 chars upper. OG image = PNG.
- `GET /certificate/<code>.png` — rendered image (§19.3). 404 for unknown code.

### 6.12 Poster — `GET /drive/<id>/poster.jpg`
Public 1080×1080 JPEG: cover image background with dark gradient, ORG name, title, date, time, venue, "Book your time", site URL. Cached.

### 6.13 Media — `GET /media/<id>` (and legacy `/media/drives/<name>`)
Serves stored image with `Cache-Control: public, max-age=31536000, immutable`. 404 if unknown.

### 6.14 Calendar feed — `GET /calendar/<cal_token>.ics`
Private subscribe URL (webcal). Donor: their booked drives (with slot times). Staff: also their tasks with due dates (and, for managers, all drives). `POST /calendar/reset` (login) regenerates the token (old URL stops working). UI "Calendar sync" dropdown: copy link, Google Calendar subscribe, Apple (webcal://), Outlook, reset.

---

## 7. Authentication

### 7.1 `GET|POST /register` (`?drive=<id>` optional)
Fields: name (≤100), email (unique, lowercased), phone/WhatsApp (required, normalised), blood group (8 options or "Not sure" = NULL), sex (Male/Female), weight (30–250, optional), dob (age 16–75, optional), password (≥8). Errors re‑render with values kept.
On success: create donor (role donor, ref_code, cal_token), attach referral from session (`referred_by`) → publish `referral.joined`, adopt guest interests with same email/phone, log in, publish `donor.registered` (welcome message). If `drive` given → create booking interest for that drive (or redirect to drive page `#book` when it has slots). Redirect to dashboard.

### 7.2 `GET|POST /login`
Email + password; "Keep me signed in for 7 days (donors only)" (staff never get remember cookie). Failure: generic "Wrong email or password". `session.clear()` before login (session fixation). Safe `next` redirect (local paths only). Staff → `/admin/`, donors → dashboard.

### 7.3 `POST /logout` (also GET tolerated)
Clears session, redirects home.

### 7.4 `GET|POST /forgot`
Email → if account exists, email a reset link; **always same answer** ("If that email is registered, a link is on its way"). Rate limit: one request per 60 s per session/email. Help text: "No email? ask an organiser".

### 7.5 `GET|POST /reset/<token>`
Token = signed `{id, fingerprint of current password hash}`, max age **1 hour**; becomes invalid after the password changes (one‑time). Form: password + repeat (client‑side match check). Success → set password, log in, flash, redirect.

### 7.6 Admin‑assisted resets
Users page: "Send reset link" (email) or "Set password" (generated temporary password `token_urlsafe(9)` shown once, or typed).

---

## 8. Donor area

### 8.1 `GET /dashboard` (login)
- Header "Hi {first name} 👋" + status message; buttons My details, Find a drive.
- **Next donation ring**: radial % of gap elapsed; "Ready to donate" or "N days to go"; text "Your first donation awaits!" / "You're eligible now 🎉" / "Eligible on 12 Mar 2027". ReminderService: `last` = last donation date; `next = last + 90 days`; `ready = today ≥ next or never donated`; `pct = elapsed/90`.
- **Digital donor card**: ORG, "Donor card", big blood group (or ?), avatar + name (link to profile), id `BC-00042`, QR code encoding `LIFEFLOW:DONOR:<id>`, "Show the QR code at the check-in desk".
- **My impact**: donations, lives touched (×3), badges earned; badge row with tooltips. Badges: First Drop (1), Life Saver (3), Regular Hero (5), Legend (10), Platinum (25).
- **My upcoming drives**: date tile, title link, venue, slot or time, status badge, "Pick a time"/"Change time", Google Cal link, cancel (×). Calendar sync dropdown.
- **Recommended for you**: upcoming drives not yet registered ("You're registered for every upcoming drive. Legend! 🏆").
- **Tasks assigned to you** (if any; volunteers *and* donors can be assignees): title, 🔥 important, drive, due, description, status button group (To do / In progress / Blocked / Done) → `POST /my-tasks/<id>/status`.
- **Invite friends**: rank badge, Friends joined / Friends donated / Points (joined + 2×donated), read‑only link `SITE_URL/join/<code>` with Copy, Share on WhatsApp, More… (share).
- **Invite leaderboard**: top 10 by points (first names only; gold/silver/bronze; "(you)" highlight).
- **My certificates & rewards**: certificate list (View, Download); vouchers (title, partner, details, validity "Valid until"/"No expiry"/"Expired", code with Copy, source drive).
- **Donation history** timeline (date, drive title or "Blood donation", venue, units).
- **Community insights**: analytics widgets visible to donors.

### 8.2 `GET|POST /profile`
Photo editor (upload/crop circle, remove) + form: name, email, phone, blood group, sex, weight, dob (shared `_donor_fields`), new password (optional, ≥8). Email must stay unique. Phone normalised. Sync contact details onto open interests.
`POST /profile/photo` (multipart `photo`) → ProfilePhoto: process as avatar (512 square WebP), replace old media, delete previous file. `POST /profile/photo/remove`.

### 8.3 `POST /my-tasks/<id>/status`
Assignee only; status ∈ todo|in_progress|blocked|done; audit event; htmx toast.

---

## 9. Staff workspace shell

Layout `app`: left sidebar menu (filtered by permission), top bar with search/command palette (**Ctrl+K**: jump to pages, drives, actions), user menu, theme toggle; idle logout after STAFF_IDLE_MINUTES (client warning + server enforcement). Menu:

| Item | Path | Requires |
|---|---|---|
| Overview | /admin/ | staff |
| Drives | /admin/drives/ | manage_drives |
| Planning | /admin/tasks/ | staff |
| Analytics | /admin/analytics/ | staff |
| Check-in | /admin/checkin/ | checkin |
| Donors | /admin/donors/ | manage_donors |
| Messages | /admin/messages/ | view_log |
| Reports & retros | /admin/reports/ | reports |
| Users & passwords | /admin/users/ | admin |
| Volunteers & admins | /admin/staff/ | admin |
| Integrations | /admin/integrations/ | admin |

### 9.1 `GET /admin/` Overview
KPI stats (donors, donations, lives, upcoming drives, open tasks), **Upcoming drives** list with fill and links, **My tasks** (due soon first), **Quick actions** (new drive, check‑in, add donor, send message, import) filtered by permission.

---

## 10. Drives (manage_drives)

### 10.1 `GET /admin/drives/` list
Upcoming and past/completed drives: date, title, venue, going/capacity, donated, status badge (open/completed), links Manage / Edit / Clone / public page.

### 10.2 `GET|POST /admin/drives/new` (also `?from=<id>` to prefill from a previous drive + show "Lessons from {drive}" = its retro to_improve/actions)
Fields: title*, venue*, drive_date*, time_slot, description, capacity; **time slots**: `use_slots` checkbox, `slot_start` (e.g. 10:00), `slot_end` (17:00), `slot_minutes` (e.g. 30), `slot_capacity` (e.g. 8) → SlotPlanner generates consecutive slots; drive capacity = sum of slot capacities. **Pictures**: up to 3 uploads (`images`), or `image_url` (http/https link), or `copy_images_from` (previous drive). **Announce**: checkbox → send `drive.created` to chosen audience (`audience` select: donors / eligible / volunteers / admins / group:X) and channels. **Social**: checkboxes per connected network → publish poster post. **Checklist**: `add_checklist` + optional `assignee` → apply playbook (§12.3).
Validation: date required and valid; slot end > start; minutes 5–240; capacity 1–500.

### 10.3 `GET /admin/drives/<id>` Manage board
Header with status, date, venue, counts; action panels:
- **Attendee board (kanban)** columns Interested / Confirmed / Donated / No‑show; cards (name, phone, blood group, slot, source badge); drag between columns → `POST /admin/drives/move` JSON `{iid, status}`. Rules (AttendanceService): `donated`/`no_show` only allowed **on the drive date** (`DAY_ONLY`); completed drive is **locked**; moving to donated creates a donation row (date = drive date) and publishes `donation.recorded` (thank‑you message); moving away from donated deletes that donation.
- **Attendee detail** `GET /admin/drives/<id>/people/<iid>` (modal/partial): contact, history, donation count, last donation, eligibility, slot selector `POST .../people/<iid>/slot` (SlotAllocator: admin may exceed capacity, others may not; notifies donor `booking.moved`).
- **Time slots** panel: table of slots with booked/capacity; per‑slot capacity `POST /admin/drives/<id>/slots/<sid>/capacity` (`value` or `delta` ±1; htmx); all slots `POST /admin/drives/<id>/slots/capacity`; regenerate `POST /admin/drives/<id>/slots` (only if no bookings, else refuse); capacity never below booked; MAX 500; drive capacity synced to sum.
- **Edit drive details** `POST /admin/drives/<id>/edit`.
- **Pictures** `POST /admin/drives/<id>/images` with `action` add (upload/url, ≤3) / remove (`which`) / cover (make first). DriveGallery keeps order; first = cover → `image_url`. Unused media deleted.
- **Announce this drive** `POST /admin/drives/<id>/notify` (audience + channels) and **Invite donors** `GET|POST /admin/drives/<id>/invite`: filters (groups, sex, eligible only, min donations, not donated since N days, age range, exclude already registered for this drive) with live count + preview list ("Who to invite"), send `drive_invitation` via chosen channels.
- **Drive checklist** `POST /admin/drives/<id>/checklist` (apply playbook, optional assignee) / remove (see tasks).
- **Clone this drive** `POST /admin/drives/<id>/clone`: new date (suggested = +7 days), copies title/venue/time/description/capacity/pictures/slots, optional checklist.
- **Publish on social media** `POST /admin/drives/<id>/social` (networks, caption editable; default from template).
- **Complete “{title}”** / Reopen / **Certificates & rewards** (§19).

---

## 11. Check‑in desk (checkin) — `/admin/checkin/?drive=<id>`
Drive selector (defaults to today's/next drive). Live list of registrations grouped/sortable by slot with search; buttons per person: Confirmed (arrived) / Donated / No‑show → `POST /admin/checkin/<d>/mark/<iid>/<status>` (same AttendanceService rules). Counters (expected, arrived, donated). Panels:
- **Lookup** `POST /admin/checkin/<d>/lookup` (`q` name/email/phone) → htmx partial results with "Check in" (adds/updates interest as confirmed, source walkin).
- **Walk‑in donor** `POST /admin/checkin/<d>/walkin` WalkInForm: name*, phone*, email (optional → placeholder `walkin-xxxx@no-email.local`), blood group, sex. Existing person matched by email or phone (last 8 digits) instead of duplicating. Checked in as confirmed, source walkin.
- **Scan donor card** `POST /admin/checkin/<d>/scan` `code` = `LIFEFLOW:DONOR:<id>` from camera QR scanner → check in. Invalid → error toast.
- Link/QR to kiosk page for self check‑in.

---

## 12. Planning / tasks

### 12.1 `GET /admin/tasks/` board
Kanban columns To do / In progress / Blocked / Done (drag → `POST /admin/tasks/move` JSON `{id, status}`); filters: scope (mine default / `all` for manage_tasks), `drive`, `who` (assignee). Visibility (TaskPolicy): admins see all; others see tasks assigned to them, created by them, or unassigned (manage_tasks sees all). Cards: title, important flame, due (overdue red), assignee avatar, drive, phase. Also calendar view (FullCalendar‑like) from `GET /admin/tasks/events.json`. Side panels: **Drive checklists** (apply/remove per drive), **How planning works** help, Mermaid **task lifecycle** diagram.
- `POST /admin/tasks/` create: title*, description, due_at, assignee (person picker `GET /admin/tasks/people` JSON search over staff and donors), drive, important, remind, phase. Publishes `task.assigned` when assignee ≠ creator.
- `POST /admin/tasks/<id>` update (same fields + status); audit events per change; reassignment notifies.
- `POST /admin/tasks/<id>/claim` assign to me (unassigned only).
- `POST /admin/tasks/<id>/delete`, `POST /admin/tasks/bulk-delete` (ids[]).
- `POST /admin/tasks/checklist/<drive_id>/remove` (`which=open` → only To do; else all checklist tasks; user's own extra tasks kept). Confirmation modal "Remove checklist".
- Task history (task_events) shown in task edit modal. Google Calendar link per task.
- Permissions: edit/delete only creator, assignee, or manage_tasks/admin.

### 12.2 Reminders
`remind=1` tasks due within 24 h, not reminded in last 12 h, not done → message `task_reminder` to assignee (important: email+sms+whatsapp; else email+whatsapp). (§23)

### 12.3 Standard drive checklist (playbook) — 28 tasks
Due = drive_date + day offset, at time (default 09:00). Applying is idempotent (matched by title). All get remind=1, status todo, phase set, created event "from checklist (phase)".

| Phase | Title | Day | Time | Important | Details |
|---|---|---|---|---|---|
| Planning | Confirm date, venue and capacity with the venue owner | −42 | | ✔ | Written confirmation of hall/room, hours, power, Wi‑Fi, parking, loading |
| Planning | Book the blood bank collection team | −35 | | ✔ | Beds, nurses/doctors, equipment, arrival time (e.g. HSA); share expected numbers |
| Planning | Book tables, chairs, screens and a rest area | −28 | | | Registration, waiting, screening, donation, rest areas |
| Planning | Set up the drive in the system with time slots | −28 | | | Slot length & donors per slot match beds; banner image |
| Planning | Recruit volunteers and assign roles | −21 | | | Registration, queue marshal, refreshments, runner, aftercare, photographer; logins |
| Promotion | Design poster and social media graphics | −21 | | | Date, venue, QR/link, chatbot |
| Promotion | Send personal invitations to eligible donors | −21 | | ✔ | Invite donors: eligible now, not registered; email + WhatsApp |
| Promotion | Post on social media and partner channels | −14 | | | Company channels, communities, partners; invite links |
| Promotion | Second invitation wave and urgent blood groups | −7 | | | Re‑invite non‑bookers; urgent groups note |
| Promotion | Check day-before reminders are going out | −2 | | | Messages page; phone unconfirmed VIP/first‑timers |
| Logistics | Order refreshments for donors | −10 | | | ~1.2 × expected donors |
| Logistics | Prepare signage, arrows and queue markers | −7 | | | |
| Logistics | Print forms and the self check-in QR poster | −5 | | | |
| Logistics | Arrange first-aid kit and emergency plan | −5 | | ✔ | |
| Logistics | Volunteer briefing | −2 | 18:00 | ✔ | Roles, flow, safety, check‑in desk use |
| Logistics | Confirm final numbers with the collection team | −2 | | ✔ | |
| Logistics | Charge devices and test check-in | −1 | 17:00 | | |
| Drive day | Venue set-up | 0 | 08:00 | ✔ | |
| Drive day | Open check-in desk and self check-in | 0 | 09:30 | | |
| Drive day | Manage queue and fit walk-ins into free slots | 0 | 10:00 | | |
| Drive day | Run refreshments and donor aftercare | 0 | 10:00 | | Rest 10–15 min, watch dizziness |
| Drive day | Mid-day headcount and update the board | 0 | 13:00 | | |
| Drive day | Pack down and hand back the venue | 0 | 18:00 | | |
| Follow-up | Mark no-shows and confirm all donations are recorded | +1 | | ✔ | |
| Follow-up | Thank donors and volunteers | +1 | | | |
| Follow-up | Share results and photos | +3 | | | |
| Follow-up | Write the drive report and retrospective | +3 | | ✔ | |
| Follow-up | Turn retro actions into tasks for the next drive | +5 | | | |

---

## 13. Donors (manage_donors)

### 13.1 `GET /admin/donors/` grid (+ `GET /admin/donors/rows` htmx partial; pushes URL via `HX-Replace-Url`)
Query params (DonorGridQuery): `q` (name/email/phone), `groups` (multi, incl. `unknown`), `status` (eligible | waiting | new = never donated), `sex`, `min_donations`, `people` (donor default | volunteer | admin | all), `sort` (name|group|donations|last|joined), `dir` (asc|desc), `page`, `per` (10–200, default 25). Facet counts per blood group and status. Columns: checkbox, avatar+name, blood group badge, phone (WhatsApp link), email, donations, last donation, eligibility status, joined. Row click → profile.
Toolbar / bulk actions on selected ids (or "all matching"):
- **Edit** `POST /admin/donors/bulk/edit` — set blood_group, sex, or role donor/volunteer (never changes admins).
- **Message** `POST /admin/donors/bulk/message` — channels + subject + text (broadcast template).
- **Invite** `POST /admin/donors/bulk/invite` — choose upcoming drive → drive_invitation.
- **Export** `POST /admin/donors/bulk/export` and `GET /admin/donors/export.xlsx` (current filter) — styled sheet (red header #E11D48, white bold, frozen header row, auto widths): Name, Email, Phone, Blood group, Sex, Weight, DOB, Donations, Last donation, Joined.
- **Saved groups** (segments): `POST /admin/donors/segments` (name + current query) / `POST /admin/donors/segments/<id>/delete`; listed as quick filters.
- **Add a donor** `POST /admin/donors/add` (DonorForm; password optional → random).
- **Add many donors** `POST /admin/donors/add-many` — spreadsheet‑like grid in the browser (JSON rows) → goes to the import review (§14).
- Blood group summary chips.

### 13.2 `GET /admin/donors/<id>` profile
Contact, photo (upload/remove by staff: `/photo`, `/photo/remove`), stats, eligibility, **Edit donor** `POST /<id>/edit`, **Record donation** `POST /<id>/donation` (date, drive optional, units) → publishes donation.recorded, **Registered drives**, **Donation history**, **Access** (admin: role, volunteer role, personal perms; link to reset password), referrals.

---

## 14. Excel import (bulk_import) — `/admin/import/`
- Required headers (exact): **Name, Email, Phone, Blood Group, Sex, Weight (kg), Date of Birth**.
- `GET /admin/import/template.xlsx` — template with header styling and dropdown validations (blood groups, sex).
- `POST /admin/import/upload` (.xlsx) → stage rows into `import_rows` with batch id; each row validated (DonorForm rules + duplicate email within file and vs existing). Header mismatch → error.
- `GET /admin/import/<batch>` review: counts valid/error/ignored; table with inline errors; **Fix** `POST /<batch>/fix/<rid>` (edit fields, revalidate), **Ignore** `POST /<batch>/ignore/<rid>`; **Commit** `POST /<batch>/commit` → create donors for valid rows; existing emails are **skipped** (status skipped); summary flash (imported/skipped).

---

## 15. Messages (view_log; sending needs notify)
### 15.1 `GET /admin/messages/`
- Channel setup status (email/SMS/WhatsApp configured or "console only"); warning if SITE_URL is localhost (links in messages won't work for recipients).
- **Compose broadcast** `POST /admin/messages/broadcast`: audience (donor | eligible | volunteer | admin | group:A+ … group:O-), optional drive, channels (email/sms/whatsapp), subject, text → Messenger to every recipient. Result flash "Sent N, logged M, failed K".
- **Test message** `POST /admin/messages/test` (admin): send to self on a channel.
- **Delivery log** table (latest first, paged): time, event, channel, recipient, subject, status badge, drive.
- Link to **Automatic messages**.

### 15.2 Automatic messages — `GET /admin/messages/automatic/`, `POST /admin/messages/automatic/<key>` (admin)
For each AUTO key: enabled toggle, channels (email/sms/whatsapp), wording **built‑in** vs **custom** (subject + text with `{placeholders}`), live preview with SAMPLE values, list of available placeholders. Stored as settings `auto.<key>.enabled|channels|subject|text`. Default channels email + whatsapp.

| Key | Trigger | Placeholders | Default custom subject / text |
|---|---|---|---|
| welcome | donor registered | first_name, name, org, link | "Welcome to {org}, {first_name} 🩸" / "Hi {first_name},\n\nWelcome to {org}! Your donor account is ready. Register for drives in one tap, track your impact and get a reminder when you can donate again.\n\nYour dashboard: {link}" |
| drive_announcement | drive created/announced | + drive_title, drive_date, drive_time, venue | "🩸 New blood drive: {drive_title}" / "Hi {first_name},\n\nA new blood drive is coming up:\n{drive_title}\n📅 {drive_date}  🕒 {drive_time}\n📍 {venue}\n\nBook your time (no queues): {link}" |
| drive_reminder | day before drive | drive… | "⏰ Tomorrow: {drive_title}" / "Hi {first_name}, see you tomorrow at {drive_title} ({drive_time}, {venue}). Eat well and drink plenty of water. Can't come? Change or cancel: {link}" |
| slot_changed | staff moved booking | drive… + slot_time | "🕒 New time for {drive_title}: {slot_time}" / "Hi {first_name}, your time for {drive_title} on {drive_date} is now {slot_time} ({venue}). Change or cancel: {link}" |
| donation_thanks | donation recorded | common | "💚 Thank you, {first_name}" / "Thank you {first_name}! Your donation can save up to 3 lives. See your impact: {link}" |
| certificate | drive completed | drive… + voucher | "🏅 Your certificate from {drive_title}" / "Thank you {first_name}! Your donation at {drive_title} can save up to 3 lives. Here is your certificate: {link}\n{voucher}" |
| eligible_again | 90 days after donation | common | "🩸 You can donate again, {first_name}" / "Hi {first_name}, you're eligible to donate again! Find a drive: {link}" |
| referral_joined | friend registered with link | common + friend | "🎉 {friend} joined with your invite" / "🎉 {friend} joined {org} with your invite! +1 point (and +2 when they donate). Leaderboard: {link}" |

Custom text rendering: `{name}` replaced only if known (unknown placeholders left as is; no template code executed). Email: paragraphs split by blank lines, HTML‑escaped, URLs linkified, wrapped in the email layout; subject defaults to first line (≤80 chars). SMS/WhatsApp: plain text. Disabled key → nothing sent.

---

## 16. Analytics — `/admin/analytics/` (staff); access matrix `/admin/analytics/access` (admin)
Widgets (ChartWidget template method: `data()` → ApexCharts/Mermaid config):
| Widget | Default audiences | Content |
|---|---|---|
| ImpactStats | public, donor, volunteer, admin | donors, donations, lives (×3), drives |
| DonationsTrend | volunteer, admin | donations per month, last 12 months (line/area) |
| BloodGroups | public, donor, volunteer, admin | donor count per group (donut) |
| DriveFunnel | volunteer, admin | registered → confirmed → donated → no‑show |
| UpcomingFill | volunteer, admin | going vs capacity per upcoming drive (bar) |
| TaskStatus | volunteer, admin | tasks by status |
| TopDonors | donor, admin | top donors by donation count (first names) |
| TopRecruiters | all | referral points leaderboard |
| TaskLifecycle | staff | Mermaid state diagram of task statuses |
| ChannelDelivery | admin | notifications by channel × status |
Admins always see all. Access matrix: checkbox grid widget × audience; saving none stores `_none`. Widgets render on home (public), dashboard (donor), analytics (staff).

---

## 17. Reports & retrospectives (reports) — `/admin/reports/`
- List of drives (completed/past first) with key numbers and rating.
- `GET /admin/reports/<drive_id>`: auto‑creates snapshot on first open. **DriveReportBuilder** stats: registered, interested, confirmed, donated, no_show, walk_ins (source walkin/kiosk), units, show_rate (donated/(registered − interested?) → donated ÷ booked), fill_rate (registered ÷ capacity), first_timers (first ever donation at this drive), blood_groups donated, slots usage (booked/capacity per slot), messages sent per channel/status, tasks done/open. Sections: Outcome, Blood groups donated, Time‑slot usage, Messages & tasks, **Retrospective** form (went_well, to_improve, actions one per line, notes, rating 1–5) `POST /admin/reports/<id>` save; `POST /<id>/refresh` re‑snapshot stats; **Turn actions into tasks** `POST /<id>/task` (action text → task, optional next drive); `GET /<id>/export.xlsx` — sheets Summary, Retro, Slots, Attendees.
- Lessons shown on "new drive from previous" page.

---

## 18. Users & staff (admin)
### 18.1 `/admin/users/` Users & passwords
Search `q`, filter `role`. List with role badge. `GET|POST /admin/users/new` (UserForm: name, email, phone optional, role, password or generated). `GET|POST /admin/users/<id>` edit (name, email, phone, role). `POST /<id>/send-reset` (email reset link; error if no real email). `POST /<id>/password` (set typed or generated temp password, shown once). Never allow an admin to demote themselves or remove the last admin.

### 18.2 `/admin/staff/` Volunteers & admins
List staff with role, volunteer role, personal perms; `POST /admin/staff/<id>` change role, staff_role_id, toggle perm. **Add a volunteer** `POST /admin/staff/new` (promote existing person by email, or create). **Volunteer roles** CRUD: `POST /admin/staff/roles` (new: name, description, perms[]), `POST /roles/<id>` edit, `POST /roles/<id>/delete` (members keep personal perms; role cleared).

---

## 19. Drive completion, certificates & vouchers (manage_drives)
### 19.1 `POST /admin/drives/<id>/complete`
Allowed on/after drive date only. Steps (DriveCompletion): close open registrations (interested/confirmed → no_show); status → completed, completed_at/by; for every donated attendee create a certificate (uuid hex, unique per donor+drive); allocate vouchers if configured; send `certificate.issued` (certificate link + voucher text) via auto‑message settings; flash summary. Completed drive = locked board, no bookings.
### 19.2 `POST /admin/drives/<id>/reopen` — status open (certificates kept).
### 19.3 `POST /admin/drives/<id>/rewards` — VoucherOffer.from_form: `voucher_on`, title, partner, details, either one **shared code** or a list of **unique codes** (one per line, allocated in order; error if fewer codes than donors), `expires` date. Can be issued at completion or afterwards (only to donors without a voucher for this drive).
**Certificate image** (A4 landscape 1754×1240 PNG): decorative border, ORG, "Certificate of Appreciation", "presented to", donor name, text about donation at drive on date, donor photo in a circle (or blood‑drop emblem), signature line, certificate number, verify URL `SITE_URL/certificate/<code>`.

---

## 20. Social publishing (manage_drives; admin config)
Networks (Strategy): **Facebook Page** (POST `/{page}/photos` with url + caption), **Instagram Business** (create media container with image_url + caption → `media_publish`), **LinkedIn Page** (register image upload → upload → create post via REST Posts API with `LinkedIn-Version`), **X** (tweet text + link; v2 `/2/tweets`), **Telegram** (`sendPhoto` to chat). Image = public poster URL (needs public SITE_URL/MEDIA_BASE_URL). Caption default from `social_caption` template (title, date, time, venue, link, hashtags). Every attempt stored in `social_posts` (status, permalink, error) and listed on the drive page.

---

## 21. Messaging engine
- **Channels**: `email` (SMTP; HTML + text), `sms` (Twilio), `whatsapp` (Twilio `whatsapp:` prefix). Unconfigured channel → print to console, log status `logged`. Errors → `failed` with no crash.
- **Messenger.send(event, person, channels, context)** renders templates and logs to `notifications`. `send_auto(key, …)` consults automatic message settings (enabled, channels, custom wording).
- **Template lookup** per channel: `messages/<event>/<channel>.<role>.j2` → `<channel>.j2` → `text.<role>.j2` → `text.j2` (role = donor/volunteer/admin variant). Email templates start with `Subject: …` on the first line; body is wrapped in `_email_layout.html` (branded header, button, footer).
- Templates exist for: broadcast, certificate, donation_thanks, drive_announcement (+ volunteer variant, whatsapp), drive_invitation, drive_reminder, eligible_again, password_reset, referral_joined, slot_changed, social_post / caption, task_assigned (+ donor variant), task_reminder (+ donor variant, whatsapp), welcome.
- **Domain events (EventBus)** → handlers: `donor.registered` → welcome; `referral.joined` → referrer notified; `donation.recorded` → donation_thanks; `booking.moved` → slot_changed; `certificate.issued` → certificate; `drive.created` → drive_announcement to audience; `task.assigned` → task_assigned to assignee.
- **Audiences**: `donor` (all donors), `eligible` (no donation in last 90 days), `volunteer`, `admin`, `group:<BG>` for each of 8 groups.
- Phone formats: messages go to normalised E.164.

---

## 22. Validation rules (shared, also emitted as HTML attributes)
- Name 1–100 chars.
- Email valid, lowercased, unique for accounts.
- **Phone**: strip spaces/dashes; Singapore 8 digits starting 3/6/8/9 → `+65XXXXXXXX`; `65XXXXXXXX` → `+65…`; overseas must be `+` and 8–15 digits; pretty print `+65 9123 4567`; matching by last 8 digits ("like").
- Weight 30–250 kg (eligibility form 20–250); age 16–75 from dob; password ≥ 8.
- Blood group ∈ 8 values or empty.
- Upload ≤ 15 MB image (JPEG/PNG/WEBP/GIF/MPO); request ≤ 25 MB.

---

## 23. Background jobs
| Job | Schedule | Behaviour |
|---|---|---|
| Task reminders | every 15 min | remind=1, status≠done, due within next 24 h (or overdue), reminded_at null or >12 h ago → send task_reminder; set reminded_at |
| Eligibility reminders | daily 09:00 | donors whose last donation was exactly 90 days ago → auto `eligible_again` |
| Drive reminders | hourly | drives tomorrow: interests interested/confirmed, reminded_at null → auto `drive_reminder`; set reminded_at |
| Backup | daily at BACKUP_HOUR (2) if BACKUP_GIT_REMOTE set | §28 |
Disabled when SCHEDULER_ENABLED off; run only once per deployment (single worker or lock).

---

## 24. Integrations page (admin) — `/admin/integrations/`
Catalog cards: **Facebook**, **Instagram**, **LinkedIn**, **X**, **Telegram**, **Email (SMTP)**, **Twilio (SMS/WhatsApp)**. Each: status (connected / not set up, source .env or app), fields (secrets masked, "leave blank to keep"), help text and step‑by‑step setup instructions, `POST /admin/integrations/<key>` save (or `disconnect`), `POST /admin/integrations/<key>/test` (e.g. Graph `/me`, LinkedIn org lookup, Telegram `getMe`, SMTP login, Twilio account fetch) with result toast. Secrets encrypted with Fernet (`enc:` prefix) derived from SECRET_KEY.

---

## 25. Referral program
`ref_code` 6 hex per donor; link `/join/<code>`; on register `referred_by` set; points = joined + 2 × friends who donated; leaderboard (top N) and my rank; referral_joined message to referrer.

## 26. Calendar & Google links
- Google Calendar template links for drives (with slot times) and tasks.
- ICS: per drive and personal feed (§6.14). Events include title, location, description, URL; times in local timezone.

---

## 27. Media
ImageProcessor: open, EXIF‑rotate, convert to RGB, drive images max side 1920, avatars center‑crop 512×512, save **WebP q82**. Key `<kind>/<id[:2]>/<id>.webp`. Storage backends LocalStorage (UPLOAD_DIR) and S3Storage (bucket, endpoint, public URL). `media_url` filter: media id → `/media/<id>` (or S3 public URL); http(s) URLs pass through; legacy `/media/drives/<name>`. Deleting a drive picture or avatar deletes the file when unused.

---

## 28. Backup & restore
- **Backup** (CLI `backup` / nightly job): export every table to `tables/<name>.json` + `manifest.json` (time, counts, schema version) and media files to `media/<key>` in BACKUP_DIR; GitPublisher clones/inits repo, commits "Backup <timestamp>", pushes to BACKUP_GIT_REMOTE/BACKUP_BRANCH.
- **Restore** (CLI `restore FOLDER [--force]`): refuses if data tables already contain rows unless `--force`; imports tables in dependency order; resets PostgreSQL sequences (`setval`); ANALYZE; copies media back.

## 29. Migrations
Forward‑only, recorded in `schema_migrations`, run at start when AUTO_MIGRATE: add missing columns (AddColumn list), add indexes, **DedupeInterests** (keep highest‑rank row per drive+donor), **SeedVolunteerRoles**, **PromoteLegacyAdmins**, **NormalizePhones** (+65), **MoveLegacyDrivePictures** (to media storage). CLI `migrate [--status]`.

## 30. CLI & scripts
`create-admin EMAIL PASSWORD`, `send-reminders` (run reminder jobs now), `backup`, `restore`, `migrate`, `seed-demo` (16 donors with mixed groups, volunteer `vol@demo.sg / demo1234`, 5 drives with 30‑min slots 10:00–17:00 capacity 8, interests, past donations, playbook tasks, referrals). Shell: `run.sh start|stop|restart|status|logs|admin|demo|backup|migrate|restore`, `setup.sh` (venv, `.env` from template, DB drivers, boto3), `seed.sh`.

---

## 31. Security requirements
- CSRF token on every POST (forms + htmx header); token never expires within the session; on CSRF failure → flash "Your session expired, please try again" and redirect back (htmx: `HX-Refresh`).
- Session: HttpOnly, SameSite=Lax, Secure when configured; lifetime 12 h; remember‑me 7 days (donors only); strong session protection; `session.clear()` on login.
- Staff idle logout after 30 min inactivity.
- Private pages send `Cache-Control: no-store`; all responses `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`.
- Passwords hashed (PBKDF2/scrypt/bcrypt). Reset tokens signed, 1 h, single‑use via hash fingerprint. Forgot‑password returns same answer and is rate limited.
- Redirect targets (`next`) must be local paths.
- Kiosk search exact match only, masked output.
- Admin can't demote self. Bulk role changes never touch admins.
- Secrets encrypted at rest; never rendered back in forms.
- Custom message wording is plain placeholders, never executable templates.
- All SQL parameterised.

---

## 32. UI conventions
- Brand: rose/red primary, rounded cards (`rounded-[2rem]`), glass cards, gradient hero, subtle "rise" entrance animations, count‑up numbers, confetti on success, light/dark theme saved per browser.
- Toasts for flashes and htmx `HX-Trigger: {"toast": {...}}`.
- Empty states with icon, title, text, CTA.
- Reusable components: avatar (photo or initials), blood‑group badge, status badge (interested=ghost, confirmed=info, donated=success, no_show=warning), fill bar, share button (Web Share API → fallback copy + WhatsApp/Facebook/X/LinkedIn/Telegram/email links), calendar‑sync dropdown, photo editor, person picker, image picker/dropzone, datatable, kanban, countdown, carousel, QR generator, QR scanner, command palette, bottom sheet on mobile.
- Date filters: nice_date "Sat, 14 Nov 2026", day "14", month "NOV", initials, pct, maps link, wa.me link, phone pretty.
- Fully responsive (mobile first); print styles for certificate.

---

## 33. Acceptance checklist (re‑implementation must pass)
- [ ] Guest can view drives, show interest, check eligibility (form + chatbot) with identical rule outcomes.
- [ ] Register (with drive and referral), login (remember donors only), forgot/reset (1 h, single use).
- [ ] Book slot, full slot rejected, change slot, cancel; capacity counts exclude no‑show.
- [ ] Dashboard ring, donor card QR `LIFEFLOW:DONOR:<id>`, badges thresholds 1/3/5/10/25, referral points, certificates, vouchers, history, tasks.
- [ ] Kiosk find/new/me check‑in with masking.
- [ ] Staff menu by permission; volunteer role ∪ personal perms; admin all.
- [ ] Drive create with slot generation, pictures ≤3, announce, social, checklist (28 items, idempotent), clone (+7 days).
- [ ] Attendance board rules: donated/no‑show only on drive day; completed locked; donation rows synced; thank‑you sent.
- [ ] Check‑in desk lookup, walk‑in dedupe, QR scan.
- [ ] Tasks board, visibility policy, claim, bulk delete, checklist remove (all/open), reminders 24 h / 12 h cooldown.
- [ ] Donor grid filters/sort/paging/facets, bulk edit/message/invite/export, segments, add many → import review.
- [ ] Excel import exact headers, validation, fix/ignore, commit skipping existing emails, template with dropdowns.
- [ ] Messages broadcast to audiences, delivery log statuses sent/logged/failed, automatic message settings with placeholders.
- [ ] Analytics widgets + access matrix.
- [ ] Reports snapshot, retro, export (4 sheets), actions → tasks.
- [ ] Completion: close open → no_show, certificates, vouchers (shared/unique), notifications, reopen.
- [ ] Public certificate page + PNG, poster JPEG, ICS feeds with reset.
- [ ] Integrations save/test/disconnect with encrypted secrets.
- [ ] Jobs, backup/restore, migrations, CLI seed‑demo.
- [ ] Security headers, CSRF, idle logout, no‑store.
