const fmt = (n, ccy) =>
  new Intl.NumberFormat("en-GB", { style: "currency", currency: ccy || "EUR" }).format(n);

function pill(text, cls) {
  return `<span class="pill ${cls || ""}">${text}</span>`;
}

function render(close) {
  const b = close.batch;
  document.getElementById("batch-title").textContent = `${b.entity} · ${b.id}`;
  const badge = document.getElementById("tieout");
  badge.textContent = `tie-out ${b.tie_out.status} · ${fmt(b.tie_out.debits, b.currency)}`;
  badge.className = `badge ${b.tie_out.status}`;
  document.getElementById("counts").innerHTML = `
    <span>${b.counts.rule} by rule</span>
    <span>${b.counts.decision} by decision</span>
    <span>${b.counts.open_case} open case</span>
  `;
  document.getElementById("lines").innerHTML = close.lines.map(lineCard).join("");
  document.querySelectorAll("[data-act]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const act = btn.getAttribute("data-act");
      const reason = document.querySelector(`textarea[data-id="${id}"]`).value.trim();
      if (act === "override" && !reason) {
        alert("Override needs a reason. That reason becomes the next decision.");
        return;
      }
      btn.closest(".card").insertAdjacentHTML(
        "beforeend",
        `<p class="reason"><strong>Recorded ${act}</strong>${reason ? " — " + reason : ""} (stays on the line; not a cell comment).</p>`
      );
    });
  });
}

function lineCard(l) {
  const origin = l.origin === "rule" ? pill(`rule ${l.rule.id} ${l.rule.version}`, "rule") : pill("decision", "decision");
  const klass = pill(l.class, l.class === "review" ? "review" : "");
  let body = "";
  if (l.rule) {
    body += `<p class="reason">Matched <strong>${l.rule.matched}</strong> via ${l.rule.id} ${l.rule.version}.</p>`;
  }
  if (l.case) {
    const c = l.case;
    body += `<p class="reason"><strong>${c.type}</strong> · ${c.id}<br/>
      Candidates: ${c.candidates.join(" · ")}<br/>
      Chosen: ${c.chosen || "— open —"}<br/>
      Author ${c.author}${c.decider ? " → decided by " + c.decider : " → awaiting admin"}<br/>
      ${c.reason}</p>`;
  }
  const actions =
    l.status === "open"
      ? `<div class="actions">
           <button class="primary" data-act="accept" data-id="${l.id}">Accept</button>
           <button data-act="reject" data-id="${l.id}">Reject</button>
           <textarea data-id="${l.id}" placeholder="Override reason (becomes a decision)"></textarea>
           <button data-act="override" data-id="${l.id}">Override</button>
         </div>`
      : `<div class="actions"><em style="color:#5b6578;font-family:ui-sans-serif,system-ui,sans-serif;font-size:13px">Already ${l.status}. Override still writes a new decision.</em>
           <textarea data-id="${l.id}" placeholder="Override reason"></textarea>
           <button data-act="override" data-id="${l.id}">Override</button>
         </div>`;
  return `<article class="card ${l.status === "open" ? "open" : ""}">
    <div class="meta">${pill(l.id)} ${origin} ${klass} ${pill(l.status)} ${pill(l.source.file + " p." + l.source.page)}</div>
    <p class="amount">${fmt(l.amount, l.currency)} <span style="color:#5b6578;font-size:14px">${l.date}</span></p>
    <div class="excerpt">${l.source.excerpt}</div>
    ${body}
    ${actions}
  </article>`;
}

fetch("/api/close")
  .then((r) => r.json())
  .then(render)
  .catch((err) => {
    document.getElementById("batch-title").textContent = "Could not load fixture";
    console.error(err);
  });
