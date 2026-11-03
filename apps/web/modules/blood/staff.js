/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Blood donation — staff: drives (create with slots + checklist, board, complete), check-in desk, donors, reports.
import { api, can, esc, run } from "../../app.js";

const COLS = ["interested", "confirmed", "donated", "no_show", "not_eligible"];

export const routes = [
  { path: "/admin/drives", nav: "Manage drives", auth: "staff", perm: "manage_drives", render: async function draw(el) {
    const drives = await api("/drives");
    el.innerHTML = `<h1>Drives</h1><form class="card" id="f"><h2>New drive</h2><div class="row"><div><label>Title</label><input name="title" required></div><div><label>Venue</label><input name="venue" required></div><div><label>Date</label><input name="drive_date" type="date" required></div></div>
      <div class="row"><div><label>Slots from</label><input name="start" value="10:00"></div><div><label>to</label><input name="end" value="17:00"></div><div><label>Minutes</label><input name="minutes" type="number" value="30"></div><div><label>Per slot</label><input name="capacity" type="number" value="8"></div></div>
      <label>Description</label><textarea name="description" rows="2"></textarea><label><input type="checkbox" name="checklist" checked style="width:auto"> Add the 28-step drive checklist</label>
      <label><input type="checkbox" name="announce" style="width:auto"> Announce to eligible donors</label><p><button class="btn primary">Create</button></p></form><br>
      <div class="card"><table><tr><th>Date</th><th>Drive</th><th>Going</th><th></th></tr>${drives.map((d) => `<tr><td>${esc(d.drive_date)}</td><td>${esc(d.title)}</td><td>${d.going}/${d.capacity}</td><td><a class="btn small" href="#/admin/drives/${d.id}">Manage</a> <a class="btn small" href="#/checkin/${d.id}">Check-in</a> <a class="btn small" href="#/reports/${d.id}">Report</a></td></tr>`).join("")}</table></div>`;
    el.querySelector("#f").onsubmit = async (e) => { e.preventDefault(); const f = Object.fromEntries(new FormData(e.target));
      const r = await run(() => api("/admin/drives", { method: "POST", body: { title: f.title, venue: f.venue, drive_date: f.drive_date, description: f.description, apply_checklist: !!f.checklist,
        slot_plan: { start: f.start, end: f.end, minutes: +f.minutes, capacity: +f.capacity } } }), "Drive created");
      if (r && f.announce) await run(() => api(`/admin/drives/${r.drive_id}/announce`, { method: "POST", body: { audience: "eligible" } }), "Announced");
      draw(el); };
  } },
  { path: "/admin/drives/:id", auth: "staff", render: async function draw(el, { args }) {
    const b = await api(`/admin/drives/${args[0]}/board`); const d = b.drive;
    el.innerHTML = `<h1>${esc(d.title)}</h1><p class="muted">${esc(d.drive_date)} · ${esc(d.venue)} · ${esc(d.state)}</p>
      <p><button class="btn" data-op="complete">Complete drive</button> <button class="btn" data-op="reopen">Reopen</button> <button class="btn" data-op="clone">Clone (+7 days)</button> <button class="btn" data-op="checklist">Add checklist</button> <a class="btn" href="#/tasks?scope=all&drive=${d.id}">Tasks</a></p>
      <div class="card"><h2>Slots</h2><div class="slots">${d.slots.map((s) => `<div class="item">${s.starts_at}<br><b>${s.booked}/${s.capacity}</b><br><button class="btn small" data-cap="${s.id}" data-d="-1">−</button><button class="btn small" data-cap="${s.id}" data-d="1">+</button></div>`).join("") || '<span class="muted">No slots</span>'}</div></div><br>
      <div class="kanban">${COLS.map((c) => `<div class="col"><b>${c.replace("_", " ")}</b> ${b.columns[c].length}${b.columns[c].map((r) => `<div class="item"><b>${esc(r.name)}</b><div class="muted">${esc(r.slot_start || "")} ${esc(r.source)}</div>
        ${COLS.filter((x) => x !== c).map((x) => `<button class="btn small" data-r="${r.id}" data-s="${x}">${x.replace("_", " ")}</button>`).join("")}</div>`).join("")}</div>`).join("")}</div>`;
    const again = () => draw(el, { args });
    el.querySelectorAll("[data-op]").forEach((x) => x.onclick = async () => { await run(() => api(`/admin/drives/${d.id}/${x.dataset.op}`, { method: "POST", body: {} }), "Done"); again(); });
    el.querySelectorAll("[data-cap]").forEach((x) => x.onclick = async () => { await run(() => api(`/admin/drives/${d.id}/slot-capacity`, { method: "POST", body: { slot_id: x.dataset.cap, delta: +x.dataset.d } })); again(); });
    el.querySelectorAll("[data-r]").forEach((x) => x.onclick = async () => { await run(() => api(`/admin/registrations/${x.dataset.r}/mark`, { method: "POST", body: { state: x.dataset.s } })); again(); });
  } },
  { path: "/checkin/:id", auth: "staff", render: async function draw(el, { args }) {
    const b = await api(`/admin/drives/${args[0]}/board`);
    el.innerHTML = `<h1>Check-in · ${esc(b.drive.title)}</h1><div class="grid"><form class="card" id="code"><h2>Scan / donor id</h2><input name="code" placeholder="LIFEFLOW:DONOR:… or donor id" autofocus><p><button class="btn primary">Check in</button></p></form>
      <form class="card" id="walk"><h2>Walk-in</h2><input name="name" placeholder="Name" required><br><br><input name="phone" placeholder="Phone" required><br><br><input name="email" placeholder="Email (optional)"><p><button class="btn">Register & check in</button></p></form></div><br>
      <div class="card"><h2>Expected</h2><table>${[...b.columns.interested, ...b.columns.confirmed].map((r) => `<tr><td>${esc(r.name)}</td><td>${esc(r.slot_start || "")}</td><td>${esc(r.state)}</td><td><button class="btn small" data-id="${r.donor_id}">Arrived</button></td></tr>`).join("")}</table></div>`;
    const go = async (body, msg) => { await run(() => api(`/admin/checkin/${args[0]}`, { method: "POST", body }), msg); draw(el, { args }); };
    el.querySelector("#code").onsubmit = (e) => { e.preventDefault(); const v = e.target.code.value.trim(); go(v.startsWith("LIFEFLOW:") ? { code: v } : { donor_id: v }, "Checked in"); };
    el.querySelector("#walk").onsubmit = (e) => { e.preventDefault(); go(Object.fromEntries(new FormData(e.target)), "Walk-in checked in"); };
    el.querySelectorAll("[data-id]").forEach((x) => x.onclick = () => go({ donor_id: x.dataset.id }, "Checked in"));
  } },
  { path: "/admin/donors", nav: "Donors", auth: "staff", perm: "manage_donors", render: async function draw(el, q) {
    const g = await api(`/admin/donors?q=${encodeURIComponent(q.q || "")}&group=${encodeURIComponent(q.group || "")}&status=${q.status || ""}&page=${q.page || 1}`);
    el.innerHTML = `<h1>Donors <span class="muted">${g.total}</span></h1><form id="s" class="card row"><input name="q" placeholder="Search name, email, phone" value="${esc(q.q || "")}">
      <select name="group"><option value="">All groups</option>${["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "unknown"].map((x) => `<option ${x === q.group ? "selected" : ""}>${x}</option>`).join("")}</select>
      <select name="status"><option value="">Any status</option>${["eligible", "waiting", "new"].map((x) => `<option ${x === q.status ? "selected" : ""}>${x}</option>`).join("")}</select><button class="btn">Filter</button></form><br>
      <div class="card"><table><tr><th>Name</th><th>Group</th><th>Phone</th><th>Email</th><th>Donations</th><th>Status</th></tr>${g.rows.map((r) => `<tr><td>${esc(r.name)}</td><td>${esc(r.blood_group || "?")}</td><td>${esc(r.phone)}</td><td>${esc(r.email)}</td><td>${r.donations}</td><td><span class="badge">${r.eligibility}</span></td></tr>`).join("")}</table></div>`;
    el.querySelector("#s").onsubmit = (e) => { e.preventDefault(); location.hash = "#/admin/donors?" + new URLSearchParams(new FormData(e.target)); };
  } },
  { path: "/reports/:id", auth: "staff", perm: "reports", render: async function draw(el, { args }) {
    const r = await api(`/admin/reports/${args[0]}`); const s = r.stats;
    el.innerHTML = `<h1>Report · ${esc(r.title)}</h1><div class="grid">${[["Registered", s.registered], ["Donated", s.donated], ["No-show", s.no_show], ["Walk-ins", s.walk_ins], ["Show rate", s.show_rate + "%"], ["Fill rate", s.fill_rate + "%"], ["First-timers", s.first_timers], ["Lives", s.lives]]
      .map(([l, v]) => `<div class="card"><div class="stat">${v}</div><div class="muted">${l}</div></div>`).join("")}</div><br>
      <form class="card" id="retro"><h2>Retrospective</h2><label>What went well</label><textarea name="went_well">${esc(r.went_well)}</textarea><label>To improve</label><textarea name="to_improve">${esc(r.to_improve)}</textarea>
      <label>Actions (one per line)</label><textarea name="actions">${esc(r.actions)}</textarea><label>Rating (1–5)</label><input name="rating" type="number" min="0" max="5" value="${esc(r.rating || 0)}">
      <p><button class="btn primary">Save</button> <button type="button" class="btn" id="tasks">Turn actions into tasks</button> <button type="button" class="btn" id="refresh">Refresh numbers</button></p></form>`;
    el.querySelector("#retro").onsubmit = (e) => { e.preventDefault(); const f = Object.fromEntries(new FormData(e.target)); f.rating = +f.rating; run(() => api(`/admin/reports/${args[0]}/retro`, { method: "PUT", body: f }), "Saved"); };
    el.querySelector("#tasks").onclick = () => run(() => api(`/admin/reports/${args[0]}/actions-to-tasks`, { method: "POST" }), "Tasks created");
    el.querySelector("#refresh").onclick = async () => { await run(() => api(`/admin/reports/${args[0]}/refresh`, { method: "POST" })); draw(el, { args }); };
  } },
];
