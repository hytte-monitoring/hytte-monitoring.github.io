/*
 * One project told as a story: the drawings, the C++, the verdict, and the design and the
 * code running side by side. The data comes from data/<name>.json, written by
 * tools/site/build_site.py; the dropdown at the top switches stories (#<name> in the URL).
 *
 * Diagrams are drawn by draw.io's own viewer from the files the verifier wrote, so they look
 * exactly as in draw.io; the live highlighting works on the viewer's graph model.
 */
"use strict";

const SITE = JSON.parse(document.getElementById("site").textContent);
const VIEWER = "https://viewer.diagrams.net/js/viewer-static.min.js";
const ACCENT = "#2563eb";
const ACCENT_SOFT = "#c7dcff";

// ── small helpers ──────────────────────────────────────────────────────────────────────

function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") e.className = v;
    else if (k === "html") e.innerHTML = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid != null && kid !== false) e.append(kid instanceof Node ? kid : String(kid));
  }
  return e;
}

/** Names compare the way the verifier compares them: case and punctuation ignored. */
const nname = (s) => (s || "").toLowerCase().replace(/[^a-z0-9]/g, "");
const pascal = (s) => s.split("_").map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join("");
const words = (s) => s.replace(/_/g, " ");

function md(text, inline = false) {
  if (!window.marked) return h(inline ? "span" : "p", {}, text || "");
  return h(inline ? "span" : "div", { class: inline ? null : "md", html: inline ? marked.parseInline(text || "") : marked.parse(text || "") });
}

function designTitle(d) {
  if (d.kind === "class") return "Class diagram";
  if (d.kind === "state") return `State machine of ${pascal(d.subject)}`;
  return `Scenario: ${words(d.subject)}`;
}

function percent(a) {
  return a == null ? "—" : `${Number.isInteger(a) ? a : a.toFixed(1)} %`;
}

function tone(report) {
  if (!report || !report.produced || report.alignment == null) return "na";
  return report.alignment >= 100 ? "ok" : "warn";
}

function sourceLink(path) {
  return SITE.repo && SITE.commit ? `${SITE.repo}/blob/${SITE.commit}/${path}` : null;
}

// ── draw.io diagrams ───────────────────────────────────────────────────────────────────

let viewerScript = null;

function loadViewer() {
  viewerScript ??= new Promise((resolve, reject) => {
    const s = h("script", { src: VIEWER });
    s.onload = resolve;
    s.onerror = () => reject(new Error("The draw.io viewer could not be loaded from viewer.diagrams.net."));
    document.head.append(s);
  });
  return viewerScript;
}

const pending = new Map();
const watcher = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (!entry.isIntersecting || entry.target.offsetWidth === 0) continue;
    watcher.unobserve(entry.target);
    pending.get(entry.target)?.();
    pending.delete(entry.target);
  }
}, { rootMargin: "300px" });

/** A diagram page, drawn once it comes near the screen. -> {el, ready: Promise<graph>} */
function diagram(xml, page, { lightbox = false, zoom = false } = {}) {
  const el = h("div", { class: "canvas" }, h("p", { class: "canvas-note" }, "Loading the diagram…"));
  let resolve;
  const ready = new Promise((r) => { resolve = r; });
  pending.set(el, () => loadViewer().then(() => {
    el.textContent = "";
    el.setAttribute("data-mxgraph", JSON.stringify({
      xml, page, toolbar: lightbox ? "zoom lightbox" : "", "toolbar-nohide": false, nav: false,
      resize: true, "auto-fit": true, "allow-zoom-in": zoom, center: true, lightbox, border: 16, "dark-mode": "light", tooltips: true,
    }));
    GraphViewer.createViewerForElement(el, (viewer) => resolve(viewer.graph));
  }).catch((err) => { el.textContent = ""; el.append(h("p", { class: "canvas-note" }, err.message)); }));
  watcher.observe(el);
  return { el, ready };
}

/** The comparison pages carry a legend box; the live panes explain their colours in words. */
function withoutLegend(xml) {
  const doc = new DOMParser().parseFromString(xml, "text/xml");
  for (const node of [...doc.querySelectorAll("[id]")]) {
    if (node.getAttribute("id").includes("-legend")) node.remove();
  }
  return new XMLSerializer().serializeToString(doc);
}

function labelOf(graph, cell) {
  if (!cell) return "";
  const div = document.createElement("div");
  div.innerHTML = graph.convertValueToString(cell) || "";
  return div.textContent.replace(/\s+/g, " ").trim();
}

function tooltipOf(cell) {
  const tip = cell && cell.value && cell.value.getAttribute ? cell.value.getAttribute("tooltip") : "";
  return (tip || "").split("\n")[0].trim();
}

function cellsOf(graph) {
  const model = graph.getModel();
  return Object.values(model.cells).filter((c) => !String(c.id).includes("legend"));
}

/** 'pay [hasItems] / charge' -> {event, guard}; mirrors parse_label in state_diagram/mermaid.py. */
function parseLabel(text) {
  const m = /^\s*([^[/]*?)\s*(?:\[\s*([^\]]*?)\s*\])?\s*(?:\/\s*(.*?))?\s*$/.exec(text || "");
  return m ? { event: (m[1] || "").replace(/\s*\(.*\)\s*$/, ""), guard: m[2] || "" } : { event: text, guard: "" };
}

/** Keeps one cell outlined (and, for a plain white shape, tinted) in a graph. */
class Marker {
  constructor(graph, width, tint) {
    this.graph = graph;
    this.tint = tint;
    this.line = new mxCellHighlight(graph, ACCENT, width);
    this.cell = null;
    this.style = null;
  }

  show(cell) {
    const model = this.graph.getModel();
    if (this.cell && this.style != null) model.setStyle(this.cell, this.style);
    this.cell = cell;
    this.style = null;
    if (cell && this.tint) {
      // draw.io writes a default fill as light-dark(#ffffff, ...); a coloured one is the verifier's.
      const fill = (this.graph.getCellStyle(cell).fillColor || "").toLowerCase();
      if (!fill || /^(#fff|#ffffff|white|default|none|light-dark\()/.test(fill)) {
        this.style = model.getStyle(cell) || "";
        model.setStyle(cell, mxUtils.setStyle(this.style, "fillColor", ACCENT_SOFT));
      }
    }
    this.line.highlight(cell ? this.graph.view.getState(cell) : null);
  }
}

// ── code ───────────────────────────────────────────────────────────────────────────────

const KEYWORDS = new Set(("alignas auto bool break case char class const constexpr continue default " +
  "delete do double else enum explicit false float for friend if inline int long namespace new " +
  "noexcept nullptr operator override private protected public return short signed sizeof static " +
  "struct switch template this true typename unsigned using virtual void while").split(" "));

function cppLine(line) {
  const frag = document.createDocumentFragment();
  const re = /(\/\/.*$|\/\*.*?\*\/)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(^\s*#\s*\w+)|\b([A-Za-z_]\w*)\b|\b(\d+)\b/g;
  let at = 0;
  let m;
  while ((m = re.exec(line))) {
    if (m.index > at) frag.append(line.slice(at, m.index));
    const cls = m[1] ? "c" : m[2] ? "s" : m[3] ? "p" : m[5] ? "n"
      : KEYWORDS.has(m[4]) ? "k" : /^[A-Z]/.test(m[4]) ? "t" : null;
    frag.append(cls ? h("span", { class: `tok-${cls}` }, m[0]) : m[0]);
    at = re.lastIndex;
  }
  frag.append(line.slice(at));
  return frag;
}

/** A source file with line numbers. -> {el, mark(line)} */
function codeBlock(text) {
  const lines = text.replace(/\n$/, "").split("\n");
  const rows = lines.map((line, i) => h("span", { class: "line", "data-n": i + 1 }, cppLine(line), "\n"));
  const el = h("pre", { class: "code", tabindex: "0" }, h("code", {}, rows));
  return {
    el,
    mark(n) {
      rows.forEach((r) => r.classList.remove("hit"));
      const row = rows[n - 1];
      if (!row) return;
      row.classList.add("hit");
      el.scrollTop = Math.max(0, row.offsetTop - el.clientHeight / 2 + row.offsetHeight);
    },
  };
}

function tabs(items, { label }) {
  // items: [{title, render: () => Node}]; renders each panel once, on first show.
  const panels = items.map(() => h("div", { class: "tab-panel", role: "tabpanel", hidden: true }));
  const buttons = items.map((item, i) => h("button", {
    class: "tab", role: "tab", type: "button", "aria-selected": "false",
    onclick: () => select(i),
  }, item.title));
  function select(i) {
    buttons.forEach((b, j) => b.setAttribute("aria-selected", String(i === j)));
    panels.forEach((p, j) => { p.hidden = i !== j; });
    if (!panels[i].firstChild) panels[i].append(items[i].render());
  }
  const el = h("div", { class: "tabs" }, h("div", { class: "tab-list", role: "tablist", "aria-label": label }, buttons), panels);
  select(0);
  return el;
}

// ── chapter 1: the drawings ────────────────────────────────────────────────────────────

function chapterDesign(story) {
  const n = story.designs.length;
  return chapter(1, "design", "A person draws the design",
    h("p", {}, n === 1 ? "One drawing, made in draw.io. " : `${n} drawings, made in draw.io. `,
      "They are the whole specification: an AI implements them, and the verifier checks the code against them, element by element."),
    story.designs.map((d) => {
      const { el } = diagram(d.input, 0, { lightbox: true });
      return h("figure", { class: "figure" }, el,
        h("figcaption", {}, h("code", {}, `diagrams/input/${d.file}`), " — ", designTitle(d).toLowerCase()));
    }));
}

// ── chapter 2: the code ────────────────────────────────────────────────────────────────

function chapterCode(story) {
  if (!story.code.length) {
    return chapter(2, "code", "An AI writes the C++", h("p", {}, "There is no implementation yet."));
  }
  const headers = story.code.filter((f) => f.path.endsWith(".hpp")).length;
  return chapter(2, "code", "An AI writes the C++",
    h("p", {}, "An AI agent implements the drawings, following ",
      h("code", {}, "AGENTS.md"), " and the UML → C++ mapping: a filled diamond becomes a ",
      h("code", {}, "std::unique_ptr"), ", a state machine a transition table, a scenario a program. ",
      `The ${headers} header${headers === 1 ? " is" : "s are"} what gets compared with the design.`),
    tabs(story.code.map((f) => ({
      title: f.path.split("/").pop(),
      render: () => {
        const link = sourceLink(`${story.path}/${f.path}`);
        return h("div", { class: "file" },
          h("div", { class: "file-path" }, h("code", {}, f.path),
            link ? h("a", { href: link, target: "_blank", rel: "noopener" }, "on GitHub") : null),
          codeBlock(f.text).el);
      },
    })), { label: "Implementation files" }));
}

// ── chapter 3: the verdict ─────────────────────────────────────────────────────────────

function verdict(d) {
  const r = d.report;
  const card = h("article", { class: `verdict tone-${tone(r)}`, id: `verdict-${d.kind}-${d.subject}` },
    h("header", {}, h("h3", {}, designTitle(d)), h("code", {}, d.file)));
  if (!r.produced) {
    card.append(h("p", { class: "verdict-none" }, `Not verified: ${r.reason}`));
    return card;
  }
  card.append(h("div", { class: "score" },
    h("span", { class: "score-value" }, percent(r.alignment)),
    h("span", { class: "score-text" }, "alignment — ", md(r.summary, true))));
  card.append(h("div", { class: "table-wrap" }, md(r.counts)));
  const none = [...r.differences.matchAll(/^#+ .*\((\d+)\)\s*$/gm)].every((m) => m[1] === "0");
  card.append(none
    ? h("p", { class: "verdict-clean" }, "No differences: the code is exactly the design.")
    : h("div", { class: "differences" }, md(r.differences)));
  card.append(h("details", {}, h("summary", {}, "What the numbers mean"), md(r.meaning)));
  if (d.kind === "class" && d.comparison) {
    card.append(comparisonTabs(d));
  } else if (d.comparison) {
    card.append(h("p", { class: "verdict-run" },
      h("a", { href: `#run-${d.kind}-${d.subject}`, onclick: jump(`run-${d.kind}-${d.subject}`) },
        "See the design and the code run side by side ↓")));
  }
  return card;
}

function comparisonTabs(d) {
  return h("div", { class: "comparison" },
    h("p", { class: "comparison-note" }, "The colour-coded comparison: amber is changed, red is missing from the code, green is extra in the code. Hover over a coloured element to see what differs."),
    tabs([
      { title: "Design (drawn)", render: () => diagram(d.comparison, 0, { lightbox: true }).el },
      { title: "Implemented (read from the code)", render: () => diagram(d.comparison, 1, { lightbox: true }).el },
    ], { label: "Comparison pages" }));
}

function chapterVerdict(story) {
  return chapter(3, "verdict", "The verifier compares them",
    h("p", {}, "The verifier reads the design back out of the code — libclang parses the headers, and every scenario is run and its calls recorded — and compares it with the drawing. No AI takes part in this step: the same drawing and the same code always give the same report."),
    h("div", { class: "verdicts" }, order(story.designs).map(verdict)));
}

// ── chapter 4: run it ──────────────────────────────────────────────────────────────────

function stateMachine(d) {
  const design = d.machines.design;
  const code = d.machines.implemented;
  const header = d.header;

  // Events: the design's, then any the code adds. Guards: every one either side uses.
  const events = new Map();
  for (const e of design.events) events.set(nname(e), { name: e, design: true, code: false });
  for (const e of code.events) {
    const known = events.get(nname(e));
    if (known) known.code = true;
    else events.set(nname(e), { name: e, design: false, code: true });
  }
  const guards = new Map();
  for (const t of [...design.transitions, ...code.transitions]) {
    if (t.guard && !guards.has(nname(t.guard))) guards.set(nname(t.guard), { name: t.guard, value: true });
  }
  const guard = (name) => guards.get(nname(name))?.value ?? true;

  // The rules of handle() in UML-CPP-MAPPING.md: the first row for this state and event
  // whose guard holds fires; an event without one is ignored.
  const step = (machine, state, event) => machine.transitions.find((t) =>
    nname(t.from) === nname(state) && nname(t.event) === nname(event) && (!t.guard || guard(t.guard))) || null;

  const now = { design: design.initial, code: code.initial };
  const live = withoutLegend(d.comparison);
  const fired = { design: null, code: null };

  const panes = ["design", "code"].map((side, page) => {
    const { el, ready } = diagram(live, page, { zoom: true });
    const pill = h("span", { class: "pill" });
    const pane = { side, el, pill, graph: null };
    ready.then((graph) => {
      const model = graph.getModel();
      pane.graph = graph;
      pane.states = new Map();
      pane.edges = [];
      for (const c of cellsOf(graph)) {
        const style = model.getStyle(c) || "";
        if (model.isVertex(c) && !/startState|endState/.test(style)) {
          const name = nname(labelOf(graph, c));
          if (name && !pane.states.has(name)) pane.states.set(name, c);
        } else if (model.isEdge(c)) {
          const src = model.getTerminal(c, true);
          const dst = model.getTerminal(c, false);
          const { event, guard: g } = parseLabel(labelOf(graph, c));
          pane.edges.push({ cell: c, from: nname(labelOf(graph, src)), to: nname(labelOf(graph, dst)), event: nname(event), guard: nname(g) });
        }
      }
      pane.state = new Marker(graph, 4, true);
      pane.edge = new Marker(graph, 4, false);
      paint();
    });
    return pane;
  });
  const [designPane, codePane] = panes;

  const findEdge = (pane, t) => {
    const hits = pane.edges.filter((e) => e.from === nname(t.from) && e.to === nname(t.to) && e.event === nname(t.event));
    return (hits.find((e) => e.guard === nname(t.guard)) || hits[0] || {}).cell || null;
  };

  const code_ = header ? codeBlock(header.text) : null;
  const log = h("ol", { class: "log", "aria-live": "polite" });
  const banner = h("p", { class: "divergence", hidden: true });
  const tableNote = h("p", { class: "code-note" });

  const buttons = [...events.values()].map((e) => h("button", {
    type: "button", class: "event", "data-event": nname(e.name), onclick: () => fire(e.name),
    title: !e.code ? "Drawn in the design, but no row of the code's table uses it" : !e.design ? "Not in the design: the code added it" : null,
  }, e.name, !e.code ? h("span", { class: "tag tag-missing" }, "missing") : !e.design ? h("span", { class: "tag tag-extra" }, "extra") : null));

  const toggles = [...guards.values()].map((g) => h("label", { class: "guard" },
    h("input", { type: "checkbox", checked: true, onchange: (ev) => { g.value = ev.target.checked; } }),
    h("code", {}, `${g.name}()`)));

  function paint() {
    for (const pane of panes) {
      const side = pane.side;
      pane.pill.textContent = now[side];
      if (!pane.graph) continue;
      pane.state.show(pane.states.get(nname(now[side])) || null);
      pane.edge.show(fired[side] ? findEdge(pane, fired[side]) : null);
    }
    const apart = nname(now.design) !== nname(now.code);
    banner.hidden = !apart;
    banner.replaceChildren("The code has left the design: the drawing is in ", h("b", {}, now.design),
      ", the code in ", h("b", {}, now.code), ". ", h("button", { type: "button", class: "link", onclick: reset }, "Start again"));
    for (const b of buttons) {
      const e = nname(b.dataset.event);
      const open = (m, s) => m.transitions.some((t) => nname(t.from) === nname(s) && nname(t.event) === e);
      b.classList.toggle("open", open(design, now.design) || open(code, now.code));
    }
  }

  const outcome = (t, from) => t ? `${from} → ${t.to}${t.action ? ` / ${t.action}()` : ""}` : `ignored in ${from}`;
  const same = (a, b) => (!a && !b) || (a && b && nname(a.to) === nname(b.to) && nname(a.action) === nname(b.action));

  function fire(event) {
    const td = step(design, now.design, event);
    const tc = step(code, now.code, event);
    const entry = same(td, tc)
      ? h("li", {}, h("b", {}, event), " ", outcome(td, now.design))
      : h("li", { class: "apart" }, h("b", {}, event),
        h("span", {}, "design: ", outcome(td, now.design)), h("span", {}, "code: ", outcome(tc, now.code)));
    log.prepend(entry);
    while (log.children.length > 12) log.lastChild.remove();
    if (code_) {
      code_.mark(tc ? tc.line : 0);
      tableNote.textContent = tc
        ? `${pascal(d.subject)}::handle() fired the row${tc.line ? ` on line ${tc.line}` : ""}.`
        : `No row of transitions[] matches ${now.code} on ${event}: handle() ignores the event.`;
    }
    fired.design = td;
    fired.code = tc;
    if (td) now.design = td.to;
    if (tc) now.code = tc.to;
    paint();
  }

  function reset() {
    now.design = design.initial;
    now.code = code.initial;
    fired.design = fired.code = null;
    log.replaceChildren();
    if (code_) {
      code_.mark(code.initialLine);
      tableNote.textContent = `A new ${pascal(d.subject)} starts in ${code.initial}${code.initialLine ? `: the initializer on line ${code.initialLine}` : ""}.`;
    }
    paint();
  }

  const el = h("section", { class: "run", id: `run-state-${d.subject}` },
    h("h3", {}, designTitle(d)),
    h("p", {}, "Fire events at both machines at once. The left one follows the drawing; the right one follows the transition table read from ",
      h("code", {}, header ? header.path.split("/").pop() : "the header"), ", with the rules of ", h("code", {}, `${pascal(d.subject)}::handle()`),
      ". Where the code differs from the design, they part ways."),
    h("div", { class: "controls" },
      h("div", { class: "control-row" }, h("span", { class: "control-label" }, "Fire an event"), buttons,
        h("button", { type: "button", class: "reset", onclick: reset }, "Reset")),
      toggles.length ? h("div", { class: "control-row" }, h("span", { class: "control-label" }, "Guards return"), toggles) : null),
    banner,
    h("div", { class: "panes" }, panes.map((p) => h("figure", { class: "pane" },
      h("figcaption", {}, p.side === "design" ? "The design, as drawn" : "The code, as implemented", p.pill), p.el))),
    h("div", { class: "below" },
      code_ ? h("div", { class: "table-code" }, h("div", { class: "file-path" }, h("code", {}, header.path)), code_.el, tableNote) : null,
      h("div", { class: "log-wrap" }, h("div", { class: "file-path" }, "What happened"), log,
        h("p", { class: "log-empty" }, "Fire an event to start."))));
  reset();
  return el;
}

/** The calls on one comparison page, in drawn order; return arrows are not compared. */
function calls(graph) {
  const model = graph.getModel();
  const edges = cellsOf(graph).filter((c) => model.isEdge(c) && labelOf(graph, c));
  const numbered = edges.map((c) => [c, /-m(\d+)$/.exec(String(c.id))]);
  const ordered = numbered.every(([, m]) => m)
    ? numbered.sort((a, b) => a[1][1] - b[1][1]).map(([c]) => c)
    : edges.sort((a, b) => graph.view.getState(a).y - graph.view.getState(b).y);
  return ordered
    .filter((c) => !/(^|;)dashed=1/.test(model.getStyle(c) || ""))
    .map((c) => {
      const text = labelOf(graph, c);
      const from = labelOf(graph, model.getTerminal(c, true));
      const to = labelOf(graph, model.getTerminal(c, false));
      return { cell: c, text, from, to, status: tooltipOf(c), key: nname(from) + ">" + nname(to) + ":" + nname(text.split("(")[0]) };
    });
}

/** Pair the drawn calls with the recorded ones (longest common subsequence), so equal calls
    share a step and a call only one side makes gets a step of its own. */
function align(a, b) {
  const n = a.length;
  const m = b.length;
  const L = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      L[i][j] = a[i].key === b[j].key ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    }
  }
  const rows = [];
  let i = 0;
  let j = 0;
  while (i < n || j < m) {
    if (i < n && j < m && a[i].key === b[j].key) rows.push({ design: a[i++], code: b[j++] });
    else if (j >= m || (i < n && L[i + 1][j] >= L[i][j + 1])) rows.push({ design: a[i++], code: null });
    else rows.push({ design: null, code: b[j++] });
  }
  return rows;
}

function scenario(d) {
  const live = withoutLegend(d.comparison);
  const panes = ["design", "code"].map((side, page) => {
    const { el, ready } = diagram(live, page, { zoom: true });
    return { side, el, ready, caption: h("p", { class: "message" }), marker: null };
  });

  let rows = null;
  let at = 0;
  let timer = null;
  const counter = h("span", { class: "counter" }, "Loading the diagrams…");

  Promise.all(panes.map((p) => p.ready)).then((graphs) => {
    graphs.forEach((graph, i) => { panes[i].marker = new Marker(graph, 5, false); });
    rows = align(calls(graphs[0]), calls(graphs[1]));
    paint();
  });

  function paint() {
    if (!rows) return;
    counter.textContent = at === 0 ? `${rows.length} steps` : `Step ${at} of ${rows.length}`;
    for (const p of panes) {
      const m = at ? rows[at - 1][p.side] : null;
      p.marker.show(m ? m.cell : null);
      p.caption.replaceChildren(at === 0 ? "Press Next or Play to start."
        : m ? h("span", {}, h("b", {}, `${m.from} → ${m.to}`), ": ", h("code", {}, m.text),
          m.status ? h("span", { class: `tag tag-${nname(m.status)}` }, m.status.toLowerCase()) : null)
          : h("span", { class: "gap" }, p.side === "design" ? "Not in the design: the code made a call the drawing does not show."
            : "The code makes no such call here."));
    }
  }
  function go(n) {
    if (!rows) return;
    at = Math.max(0, Math.min(rows.length, n));
    paint();
  }
  function play() {
    if (timer) return stop();
    if (!rows) return;
    if (at >= rows.length) at = 0;
    playButton.textContent = "Pause";
    timer = setInterval(() => (at >= rows.length ? stop() : go(at + 1)), 1400);
    go(at + 1);
  }
  function stop() {
    clearInterval(timer);
    timer = null;
    playButton.textContent = "Play";
  }
  const playButton = h("button", { type: "button", class: "event open", onclick: play }, "Play");

  const program = d.program ? d.program.path : `impl/scenarios/${d.subject}.cpp`;
  return h("section", { class: "run", id: `run-sequence-${d.subject}` },
    h("h3", {}, designTitle(d)),
    h("p", {}, "Step through the scenario. The left shows the calls as drawn; the right, the calls recorded while ",
      h("code", {}, program), " ran in an instrumented build. Equal calls share a step; a call only one side makes gets a step of its own."),
    h("div", { class: "controls" }, h("div", { class: "control-row" },
      h("button", { type: "button", class: "event", onclick: () => { stop(); go(0); } }, "Reset"),
      h("button", { type: "button", class: "event", onclick: () => { stop(); go(at - 1); } }, "◀ Back"),
      h("button", { type: "button", class: "event open", onclick: () => { stop(); go(at + 1); } }, "Next ▶"),
      playButton, counter)),
    h("div", { class: "panes" }, panes.map((p) => h("figure", { class: "pane" },
      h("figcaption", {}, p.side === "design" ? "The scenario, as drawn" : "The calls, as recorded"), p.caption, p.el))));
}

function chapterRun(story) {
  const runs = order(story.designs).filter((d) => d.comparison
    && ((d.kind === "state" && d.machines) || d.kind === "sequence"));
  if (!runs.length) return null;
  return chapter(4, "run", "See it run",
    runs.map((d) => (d.kind === "state" ? stateMachine(d) : scenario(d))));
}

// ── the story ──────────────────────────────────────────────────────────────────────────

/** State machines and scenarios first: they are what an example is about. */
function order(designs) {
  const rank = { state: 0, sequence: 1, class: 2 };
  return [...designs].sort((a, b) => rank[a.kind] - rank[b.kind]);
}

function jump(id) {
  return (ev) => {
    ev.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
}

function chapter(n, id, title, ...body) {
  return h("section", { class: "chapter", id: `ch-${id}` },
    h("h2", {}, h("span", { class: "chapter-n" }, n), title), body);
}

function hero(story, index) {
  const [num, name] = story.title.includes(" · ") ? story.title.split(" · ") : [null, story.title];
  const isExample = story.path.startsWith("examples/");
  return h("header", { class: "hero" },
    h("p", { class: "eyebrow" }, isExample ? `Example ${num || index + 1} of ${SITE.stories.filter((s) => s.path.startsWith("examples/")).length}` : "Your project",
      " · ", h("code", {}, story.path)),
    h("h1", {}, name),
    story.lead ? md(story.lead) : null,
    h("ul", { class: "scores" }, order(story.designs).map((d) => h("li", {},
      h("a", { class: `chip tone-${tone(d.report)}`, href: `#verdict-${d.kind}-${d.subject}`, onclick: jump(`verdict-${d.kind}-${d.subject}`) },
        h("span", {}, designTitle(d)), h("b", {}, d.report.produced ? percent(d.report.alignment) : "not verified"))))),
    h("nav", { class: "chapters", "aria-label": "Chapters" },
      [["design", "1 · The design"], ["code", "2 · The code"], ["verdict", "3 · The verdict"], ["run", "4 · See it run"]]
        .map(([id, text]) => h("a", { href: `#ch-${id}`, "data-chapter": id, onclick: jump(`ch-${id}`) }, text))));
}

function neighbours(index) {
  const prev = SITE.stories[index - 1];
  const next = SITE.stories[index + 1];
  const link = (s, text) => h("a", { href: `#${s.name}` }, h("span", {}, text), h("b", {}, s.title));
  return h("nav", { class: "neighbours", "aria-label": "Other stories" },
    prev ? link(prev, "← Previous") : h("span"), next ? link(next, "Next →") : h("span"));
}

const cache = new Map();

async function show(name) {
  const index = SITE.stories.findIndex((s) => s.name === name);
  const main = document.getElementById("story");
  picker.value = name;
  if (!cache.has(name)) {
    cache.set(name, fetch(`data/${encodeURIComponent(name)}.json`).then((r) => {
      if (!r.ok) throw new Error(`data/${name}.json: HTTP ${r.status}`);
      return r.json();
    }));
  }
  let story;
  try {
    story = await cache.get(name);
  } catch (err) {
    cache.delete(name);
    main.replaceChildren(h("p", { class: "error" }, `This story could not be loaded (${err.message}).`));
    return;
  }
  if (picker.value !== name) return;   // another story was picked meanwhile
  pending.clear();
  watcher.disconnect();
  const run = chapterRun(story);
  main.replaceChildren(...[hero(story, index), chapterDesign(story), chapterCode(story), chapterVerdict(story), run,
    neighbours(index)].filter(Boolean));
  if (!run) main.querySelector('[data-chapter="run"]').remove();
  document.title = `${story.title} — UML design verification`;
  window.scrollTo(0, 0);
}

function current() {
  const name = decodeURIComponent(location.hash.slice(1));
  return SITE.stories.some((s) => s.name === name) ? name : SITE.start;
}

const picker = document.getElementById("picker");
const groups = [["examples/", "Examples"], ["", "Your project"]];
for (const [prefix, label] of groups) {
  const members = SITE.stories.filter((s) => (prefix ? s.path.startsWith(prefix) : !s.path.startsWith("examples/")));
  if (members.length) picker.append(h("optgroup", { label }, members.map((s) => h("option", { value: s.name }, s.title))));
}
picker.addEventListener("change", () => { location.hash = picker.value; });
window.addEventListener("hashchange", () => show(current()));

const repoLink = document.getElementById("repo");
if (SITE.repo) repoLink.href = SITE.repo;
else repoLink.remove();

const commit = SITE.commit ? SITE.commit.slice(0, 7) : null;
document.getElementById("footer").append(
  h("p", {}, "Built ", SITE.built, commit ? [" from commit ", SITE.repo
    ? h("a", { href: `${SITE.repo}/commit/${SITE.commit}` }, h("code", {}, commit)) : h("code", {}, commit)] : null,
  SITE.ci ? [". Every report and comparison on this page was regenerated by ", h("code", {}, "tools/verify.py"), " in that build."] : "."));

show(current());
