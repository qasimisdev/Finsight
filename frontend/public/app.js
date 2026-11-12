// All requests go to /api/*; nginx forwards them to the FastAPI backend.
const API = "/api";
const chatEl = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const bgToggle = document.getElementById("bg");
const statusEl = document.getElementById("status");

let history = []; // [{role, content}]

const SUGGESTIONS = [
  "Show AAPL candlestick chart for 6 months and its RSI",
  "Compare AAPL, MSFT and NVDA over 1 year",
  "Fundamentals and valuation of TSLA",
  "If I invest $500 monthly in SPY for 10 years at 8% yearly return, what do I end up with?",
];

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function scrollDown() {
  const main = document.querySelector("main");
  main.scrollTop = main.scrollHeight;
}

function addMessage(role) {
  const wrap = el("div", `msg ${role}`);
  const bubble = el("div", "bubble");
  wrap.appendChild(bubble);
  chatEl.appendChild(wrap);
  scrollDown();
  return bubble;
}

function makeTable(rows, headers) {
  const t = el("table");
  const head = el("tr");
  headers.forEach((h) => head.appendChild(el("th", null, h)));
  t.appendChild(head);
  rows.forEach((r) => {
    const tr = el("tr");
    r.forEach((c) => tr.appendChild(el("td", null, c === null || c === undefined ? "n/a" : String(c))));
    t.appendChild(tr);
  });
  return t;
}

function fmt(n) {
  if (typeof n !== "number") return n;
  return Math.abs(n) >= 1e9 ? (n / 1e9).toFixed(2) + "B" : Math.abs(n) >= 1e6 ? (n / 1e6).toFixed(2) + "M" : n;
}

function renderTrace(bubble, trace) {
  (trace || []).forEach((step) => {
    const d = step.output || {};
    if (step.tool === "get_price_history" && d.rows) {
      const box = el("div", "chart");
      bubble.appendChild(box);
      const x = d.rows.map((r) => r.date);
      Plotly.newPlot(
        box,
        [
          { type: "candlestick", x, open: d.rows.map((r) => r.open), high: d.rows.map((r) => r.high),
            low: d.rows.map((r) => r.low), close: d.rows.map((r) => r.close), name: d.symbol, yaxis: "y" },
          { type: "bar", x, y: d.rows.map((r) => r.volume), name: "Volume", yaxis: "y2", opacity: 0.35 },
        ],
        {
          title: `${d.symbol} (${d.period})`,
          xaxis: { rangeslider: { visible: false } },
          yaxis: { domain: [0.28, 1] },
          yaxis2: { domain: [0, 0.22] },
          showlegend: false,
          margin: { t: 40, r: 10, l: 50, b: 30 },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          font: { color: getComputedStyle(document.body).color },
        },
        { responsive: true }
      );
    } else if (step.tool === "compare_stocks" && d.comparison) {
      const rows = Object.entries(d.comparison).map(([s, v]) => [s, v.return_pct, v.volatility_pct]);
      bubble.appendChild(makeTable(rows, ["Symbol", `Return % (${d.period})`, "Volatility % (annualised)"]));
    } else if (step.tool === "get_indicators" && d.latest) {
      bubble.appendChild(makeTable(Object.entries(d.latest), [`${d.symbol} indicator`, "Latest"]));
    } else if (step.tool === "get_fundamentals" && d.fundamentals) {
      const rows = Object.entries(d.fundamentals)
        .filter(([, v]) => typeof v !== "object" || v === null)
        .map(([k, v]) => [k, fmt(v)]);
      bubble.appendChild(makeTable(rows, [`${d.symbol} fundamentals`, "Value"]));
    }
  });
  if (trace && trace.length) {
    const det = el("details");
    det.appendChild(el("summary", null, `Tools used (${trace.length})`));
    const pre = el("pre");
    pre.textContent = trace.map((s) => `${s.tool}(${JSON.stringify(s.input)})`).join("\n");
    det.appendChild(pre);
    bubble.appendChild(det);
  }
}

function renderAnswer(bubble, out) {
  bubble.innerHTML = DOMPurify.sanitize(marked.parse(out.answer || "(no answer)"));
  renderTrace(bubble, out.trace);
  scrollDown();
}

async function api(path, options) {
  const res = await fetch(API + path, options);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

const post = (path, body) =>
  api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

async function runJob(payload, bubble) {
  const { job_id } = await post("/jobs", payload);
  for (let i = 0; i < 240; i++) {
    await new Promise((r) => setTimeout(r, 1500));
    const s = await api(`/jobs/${job_id}`);
    if (s.state === "SUCCESS") return s.result;
    if (s.state === "FAILURE") throw new Error(s.error || "job failed");
    const note = s.progress && s.progress.note ? s.progress.note : s.state.toLowerCase();
    bubble.replaceChildren(el("span", "dots", `Background job ${job_id.slice(0, 8)}: ${note}`));
  }
  throw new Error("Job timed out");
}

async function send(text) {
  addMessage("user").textContent = text;
  const bubble = addMessage("assistant");
  bubble.appendChild(el("span", "dots", "Fetching data and analysing"));
  sendBtn.disabled = true;
  const payload = { message: text, history: history.slice(-20) };
  try {
    const out = bgToggle.checked ? await runJob(payload, bubble) : await post("/chat", payload);
    renderAnswer(bubble, out);
    history.push({ role: "user", content: text }, { role: "assistant", content: out.answer || "" });
  } catch (e) {
    bubble.replaceChildren(el("span", "error", `Something went wrong: ${e.message}`));
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  send(text);
});

const chips = document.getElementById("chips");
SUGGESTIONS.forEach((s) => {
  const c = el("button", "chip", s);
  c.type = "button";
  c.addEventListener("click", () => { input.value = s; input.focus(); });
  chips.appendChild(c);
});

(async function checkHealth() {
  try {
    await api("/health");
    statusEl.textContent = "backend: connected";
    statusEl.className = "status ok";
  } catch {
    statusEl.textContent = "backend: unreachable";
    statusEl.className = "status down";
  }
})();
