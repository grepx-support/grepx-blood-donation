/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Blood donation — the donor's own area: dashboard (card + QR, countdown, badges, bookings, rewards, invites) and profile.
import { api, esc, run } from "../../app.js";

export const routes = [
  { path: "/dashboard", nav: "My dashboard", auth: "user", render: async (el) => {
    const d = await api("/me/dashboard"); const s = d.stats;
    el.innerHTML = `<h1>Hi ${esc((d.donor?.name || "").split(" ")[0])} 👋</h1><div class="grid">
      <div class="card-donor"><div><div class="muted" style="color:#fff">Donor card</div><div class="stat">${esc(d.donor?.blood_group || "?")}</div><b>${esc(d.donor?.name)}</b><div>${esc(d.card.number)}</div><small>Show the QR at check-in</small></div><div class="qr" id="qr"></div></div>
      <div class="card"><h2>Next donation</h2><div class="stat">${s.ready ? "Ready" : s.days_left + " days"}</div><p class="muted">${s.first ? "Your first donation awaits!" : s.ready ? "You're eligible now 🎉" : "Eligible on " + esc(s.next_eligible)}</p></div>
      <div class="card"><h2>My impact</h2><div class="stat">${s.count || 0}</div><p class="muted">donations · ${(s.count || 0) * 3} lives touched</p><p>${(s.badges || []).map((b) => `<span class="badge">🏅 ${esc(b)}</span>`).join(" ")}</p></div></div><br>
      <div class="grid"><div class="card"><h2>My drives</h2>${d.registrations.map((r) => `<div class="item"><a href="#/drives/${r.drive_id}"><b>${esc(r.drive.title)}</b></a> <span class="badge">${esc(r.state)}</span><div class="muted">${esc(r.drive.drive_date)} ${esc(r.slot_start || "")}</div></div>`).join("") || '<p class="muted">None yet.</p>'}
        <p><a href="${esc(d.calendar_url)}">Subscribe to my calendar</a></p></div>
      <div class="card"><h2>Recommended</h2>${d.recommended.map((r) => `<div class="item"><a href="#/drives/${r.id}">${esc(r.title)}</a><div class="muted">${esc(r.drive_date)}</div></div>`).join("") || '<p class="muted">You are on every drive 🏆</p>'}</div>
      <div class="card"><h2>Invite friends</h2><p class="muted">+1 point per friend who joins, +2 when they donate.</p><input readonly value="${esc(d.invite.link)}"><p><b>${d.invite.points || 0}</b> points</p>
        <ol>${d.leaderboard.map((l) => `<li>${esc(l.name)} — ${l.points} ${l.me ? "(you)" : ""}</li>`).join("")}</ol></div></div><br>
      <div class="grid"><div class="card"><h2>Certificates & rewards</h2>${d.certificates.map((c) => `<div class="item"><a href="#/certificate/${c.id}">${esc(c.drive_title)}</a></div>`).join("")}
        ${d.vouchers.map((v) => `<div class="item">🎁 <b>${esc(v.title)}</b> ${esc(v.partner || "")} <code>${esc(v.code)}</code></div>`).join("") || (d.certificates.length ? "" : '<p class="muted">Appear after each drive.</p>')}</div>
      <div class="card"><h2>Donation history</h2>${d.history.map((h) => `<div class="item">${esc(h.donated_on)} · ${esc(h.drive_title || "Blood donation")}</div>`).join("") || '<p class="muted">Your story starts here.</p>'}</div>
      ${d.tasks.length ? `<div class="card"><h2>My tasks</h2>${d.tasks.map((t) => `<div class="item">${esc(t.title)} <span class="muted">${esc(t.due_at || "")}</span></div>`).join("")}</div>` : ""}</div>`;
    if (window.QRCode) new QRCode(el.querySelector("#qr"), { text: d.card.qr, width: 96, height: 96 });
  } },
  { path: "/profile", nav: "My details", auth: "user", render: async (el) => {
    const me = await api("/me");
    el.innerHTML = `<form class="card" id="f" style="max-width:560px;margin:auto"><h1>My details</h1>${["name", "email", "phone", "dob", "weight"].map((k) => `<label>${k}</label><input name="${k}" value="${esc(me[k] ?? "")}" ${k === "dob" ? 'type="date"' : ""}>`).join("")}
      <label>Blood group</label><select name="blood_group">${["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((g) => `<option ${g === me.blood_group ? "selected" : ""}>${g}</option>`).join("")}</select>
      <label>Photo</label><input type="file" id="photo" accept="image/*"><p><button class="btn primary">Save</button></p></form>`;
    el.querySelector("#photo").onchange = (e) => { const form = new FormData(); form.append("file", e.target.files[0]); run(() => api("/me/photo", { method: "POST", form }), "Photo saved"); };
    el.querySelector("#f").onsubmit = (e) => { e.preventDefault(); const body = Object.fromEntries([...new FormData(e.target)].filter(([, v]) => v !== "")); run(() => api("/me/profile", { method: "PATCH", body }), "Saved"); };
  } },
];
