// Blood donation — public pages: home, drive + booking, sign-up, eligibility (form + LifeBot), certificate, kiosk.
import { api, esc, login, run, state } from "../../app.js";

const when = (d) => new Date(d + "T00:00").toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
const driveCard = (d) => `<a class="card" href="#/drives/${d.id}" style="color:inherit">${d.image_url ? `<img src="${esc(d.image_url)}" style="width:100%;border-radius:10px;aspect-ratio:16/9;object-fit:cover">` : ""}
  <span class="badge">${when(d.drive_date)}</span><h2>${esc(d.title)}</h2><div class="muted">📍 ${esc(d.venue)} · 🕒 ${esc(d.time_slot || "All day")}</div>
  <div class="muted">${d.going}/${d.capacity} going</div></a>`;

export const routes = [
  { path: "/", nav: "Drives", render: async (el) => {
    const [drives, stats] = await Promise.all([api("/drives"), api("/stats")]);
    el.innerHTML = `<div class="hero"><h1>${esc(state.product.tagline)}</h1><p>Find a drive, book a time, check if you can donate. One donation can save up to three lives.</p>
      <a class="btn" href="#/eligibility">Can I donate?</a> ${state.me ? "" : '<a class="btn" href="#/register">Become a donor</a>'}
      <p>Urgently needed: ${stats.urgent.map((g) => `<span class="badge" style="background:#fff">${g}</span>`).join(" ")}</p></div>
      <div class="grid">${[["Registered donors", stats.donors], ["Donations", stats.donations], ["Lives touched", stats.lives], ["Upcoming drives", stats.drives]]
        .map(([l, v]) => `<div class="card"><div class="stat">${v}</div><div class="muted">${l}</div></div>`).join("")}</div>
      <h2 style="margin-top:24px">Upcoming drives</h2><div class="grid">${drives.map(driveCard).join("") || '<p class="muted">No drives yet — sign up and we will tell you.</p>'}</div>`;
  } },
  { path: "/drives/:id", render: async function draw(el, { args }) {
    const d = await api(`/drives/${args[0]}`);
    const mine = d.my_registration && d.my_registration.state !== "cancelled" ? d.my_registration : null;
    el.innerHTML = `<div class="hero"><span class="badge" style="background:#fff">${when(d.drive_date)}</span><h1>${esc(d.title)}</h1><p>📍 ${esc(d.venue)} · 🕒 ${esc(d.time_slot || "All day")}</p></div>
      <div class="grid"><div class="card"><h2>About</h2><p>${esc(d.description || "Walk-ins welcome; booking ahead helps us plan.")}</p>
        <h2>Before you come</h2><ul><li>Eat a proper meal 3 hours before</li><li>Drink 500 ml of water</li><li>Bring your NRIC or ID</li><li>Sleep well</li></ul>
        <a class="btn" target="_blank" href="https://maps.google.com/?q=${encodeURIComponent(d.venue)}">Directions</a> <a class="btn" href="#/kiosk/${d.id}">At the venue? Check in</a></div>
      <div class="card"><h2>${mine ? `You're ${esc(mine.state)}${mine.slot_start ? ` at ${esc(mine.slot_start)}` : ""}` : "Book a time"}</h2>
        ${d.slots.length ? `<div class="slots">${d.slots.map((s) => { const left = s.capacity - s.booked; return `<button class="btn ${mine?.slot_id === s.id ? "on" : ""}" data-slot="${s.id}" ${left <= 0 && mine?.slot_id !== s.id ? "disabled" : ""}>${s.starts_at}<br><small>${left > 0 ? left + " left" : "Full"}</small></button>`; }).join("")}</div>` : ""}
        <p>${state.me ? (d.slots.length ? "" : '<button class="btn primary" id="go">I\'m going</button>') : '<a class="btn primary" href="#/register">Sign up to book</a> <a href="#/login">Log in</a>'}
        ${mine ? '<button class="btn" id="cancel">Cancel my booking</button>' : ""}</p>
        ${!state.me ? `<form id="interest"><h2>Not sure yet?</h2><div class="row"><input name="name" placeholder="Name" required><input name="phone" placeholder="Phone"></div><input name="email" placeholder="Email"><p><button class="btn">Show interest</button></p></form>` : ""}</div></div>`;
    const book = async (slot_id) => { if (!state.me) return (location.hash = "#/login"); if (await run(() => api(`/me/drives/${d.id}/book`, { method: "POST", body: { slot_id } }), "Booked — see you there!")) draw(el, { args }); };
    el.querySelectorAll("[data-slot]").forEach((b) => b.onclick = () => book(b.dataset.slot));
    el.querySelector("#go")?.addEventListener("click", () => book(""));
    el.querySelector("#cancel")?.addEventListener("click", async () => { await run(() => api(`/me/drives/${d.id}/cancel`, { method: "POST", body: {} }), "Cancelled"); draw(el, { args }); });
    el.querySelector("#interest")?.addEventListener("submit", (e) => { e.preventDefault(); const f = Object.fromEntries(new FormData(e.target)); run(() => api(`/drives/${d.id}/interest`, { method: "POST", body: f }), "Thanks! We'll keep you posted."); });
  } },
  { path: "/register", render: (el, q) => {
    el.innerHTML = `<div class="card" style="max-width:560px;margin:auto"><h1>Become a donor</h1><form id="f">
      <label>Full name</label><input name="name" required><div class="row"><div><label>Email</label><input name="email" type="email" required></div><div><label>Phone / WhatsApp</label><input name="phone" required placeholder="9123 4567"></div></div>
      <div class="row"><div><label>Blood group</label><select name="blood_group"><option value="">Not sure</option>${["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((g) => `<option>${g}</option>`).join("")}</select></div>
      <div><label>Sex</label><select name="sex"><option>Female</option><option>Male</option></select></div><div><label>Date of birth</label><input name="dob" type="date"></div></div>
      <label>Password (8+)</label><input name="password" type="password" minlength="8" required><input type="hidden" name="invite_code" value="${esc(q.ref || "")}">
      <p><button class="btn primary">Create my account</button></p></form></div>`;
    el.querySelector("#f").onsubmit = async (e) => { e.preventDefault(); const s = await run(() => api("/auth/register", { method: "POST", body: Object.fromEntries(new FormData(e.target)) }));
      if (s) { await login(s); location.hash = "#/dashboard"; } };
  } },
  { path: "/join/:code", render: (el, { args }) => { location.hash = `#/register?ref=${args[0]}`; } },
  { path: "/eligibility", nav: "Can I donate?", render: (el) => {
    let chatState = {};
    el.innerHTML = `<h1>Can I donate today?</h1><div class="grid"><div class="card"><h2>Chat with LifeBot</h2><div class="chat" id="chat"></div><div id="opts"></div>
      <form id="say" class="row"><input name="m" placeholder="Type an answer"><button class="btn primary">Send</button></form></div>
      <form class="card" id="f"><h2>Quick form</h2><div class="row"><div><label>Date of birth</label><input name="dob" type="date" required></div><div><label>Weight (kg)</label><input name="weight" type="number" required></div></div>
      <label>Sex</label><select name="sex"><option>Female</option><option>Male</option></select>
      ${[["illness", "Cold, cough or diarrhoea in the last 7 days"], ["fever", "Fever in the last 4 weeks"], ["tattoo", "Tattoo or piercing in 6 months"], ["pregnant", "Pregnant or breastfeeding"], ["medication", "Antibiotics or blood thinners"], ["travel", "Trip to a malaria/Zika area"]]
        .map(([k, l]) => `<label><input type="checkbox" name="${k}" value="yes" style="width:auto"> ${l}</label>`).join("")}<p><button class="btn primary">Check</button></p><div id="res"></div></form></div>`;
    const chat = el.querySelector("#chat");
    const say = async (message) => {
      if (message) chat.insertAdjacentHTML("beforeend", `<div class="bubble me">${esc(message)}</div>`);
      const r = await run(() => api("/eligibility/chat", { method: "POST", body: { message, state: chatState } })); if (!r) return;
      chatState = r.state; chat.insertAdjacentHTML("beforeend", `<div class="bubble bot">${esc(r.reply.reply)}</div>`); chat.scrollTop = 1e6;
      el.querySelector("#opts").innerHTML = (r.reply.options || []).map((o) => `<button class="btn small">${esc(o)}</button>`).join(" ");
      el.querySelectorAll("#opts button").forEach((b) => b.onclick = () => say(b.textContent));
    };
    say("");
    el.querySelector("#say").onsubmit = (e) => { e.preventDefault(); const v = e.target.m.value; e.target.reset(); say(v); };
    el.querySelector("#f").onsubmit = async (e) => { e.preventDefault(); const r = await run(() => api("/eligibility/check", { method: "POST", body: Object.fromEntries(new FormData(e.target)) }));
      if (r) el.querySelector("#res").innerHTML = r.eligible ? '<p class="ok"><b>You look eligible!</b> The nurse makes the final call.</p>' : `<p class="bad"><b>Not right now:</b></p><ul>${r.reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` + r.notes.map((n) => `<p class="muted">${esc(n)}</p>`).join(""); };
  } },
  { path: "/certificate/:code", render: async (el, { args }) => {
    const c = await api(`/certificates/${args[0]}`);
    el.innerHTML = `<div class="card" style="text-align:center;padding:40px"><p class="muted">Certificate of appreciation · No. ${esc(c.number)}</p><h1>${esc(c.name)}</h1>
      <p>donated blood at <b>${esc(c.drive_title)}</b> on ${when(c.donated_on)}.</p><p class="ok">✔ Verified by ${esc(state.product.name)}</p><button class="btn" onclick="print()">Print / PDF</button></div>`;
  } },
  { path: "/kiosk/:id", render: (el, { args }) => {
    el.innerHTML = `<div class="card" style="max-width:520px;margin:auto"><h1>Welcome — check in</h1><form id="find" class="row"><input name="contact" placeholder="Your phone or email" required><button class="btn primary">Find me</button></form><div id="found"></div>
      <h2>New here?</h2><form id="new"><input name="name" placeholder="Full name" required><br><br><input name="phone" placeholder="Phone" required><br><br><input name="email" placeholder="Email (optional)"><p><button class="btn">Register & check in</button></p></form></div>`;
    el.querySelector("#find").onsubmit = async (e) => { e.preventDefault(); const r = await run(() => api(`/drives/${args[0]}/kiosk/find`, { method: "POST", body: { contact: e.target.contact.value } }));
      if (!r) return; el.querySelector("#found").innerHTML = `<div class="item"><b>${esc(r.name)}</b> <span class="muted">${esc(r.phone)} ${esc(r.blood_group)}</span> <button class="btn primary" id="ci">Check in</button></div>`;
      el.querySelector("#ci").onclick = () => run(() => api(`/drives/${args[0]}/kiosk/checkin`, { method: "POST", body: { donor_id: r.donor_id } }), "You're checked in — please take a seat."); };
    el.querySelector("#new").onsubmit = (e) => { e.preventDefault(); run(() => api(`/drives/${args[0]}/kiosk/register`, { method: "POST", body: Object.fromEntries(new FormData(e.target)) }), "Welcome! You're checked in."); };
  } },
];
