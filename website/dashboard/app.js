// The dashboard page: connects the board (serial.js) to the database (db.js) and draws them.
// The ?v= numbers make browsers load new versions instead of old cached copies.
// Raise them together with the one in index.html after changing these files.
import { Board } from "./serial.js?v=2";
import * as store from "./db.js?v=2";
import { drawBarChart, drawLineChart } from "./charts.js?v=2";

const $ = (id) => document.getElementById(id);
const board = new Board();
let session = null;
let helloTimer = null;   // shows the "not running Hytte" notice if no hello arrives

// After connecting, the board restarts and greets with "hello". No greeting means the
// micro:bit runs some other program: point the user to the install page.
function expectHello() {
    clearTimeout(helloTimer);
    $("not-hytte").hidden = true;
    helloTimer = setTimeout(() => {
        $("not-hytte").hidden = false;
    }, 5000);
}

// ---------------------------------------------------------------- the LED matrix mirror

// 5x5 patterns for the board's "display" lines (firmware/src/io/output_driver.cpp).
const GLYPHS = {
    "?": ["01110", "10001", "00110", "00000", "00100"],
    H: ["10001", "10001", "11111", "10001", "10001"],
    A: ["01110", "10001", "11111", "10001", "10001"],
    warning: ["00100", "00100", "00100", "00000", "00100"],
    critical: ["11111", "11111", "11111", "11111", "11111"],
    tick: ["00000", "00001", "00010", "10100", "01000"],
};

function drawMatrix(pattern) {
    const rows = GLYPHS[pattern] ?? GLYPHS["?"];
    const matrix = $("matrix");
    matrix.replaceChildren(...rows.join("").split("").map((on) => {
        const led = document.createElement("span");
        led.className = on === "1" ? "led on" : "led";
        return led;
    }));
    matrix.dataset.pattern = pattern;
}

// ---------------------------------------------------------------- live sensor readings

// The latest readings, newest first, in this page's memory only: not stored, gone after a
// reload. The chart shows all of them (3 minutes at one reading per 2 s), the log the newest 20.
const CHART_SIZE = 90;
const SENSOR_LOG_SIZE = 20;
const readings = [];

// The latest temperature reading, as a plain number.
function drawTemperatureFigures() {
    $("temp-now").textContent = readings.length ? `${readings[0].temperature} °C` : "—";
}

// The waveform's bar heights follow the sound level: 30 dB (quiet) is flat, 80 dB is full.
const WAVE = [0.3, 0.5, 0.4, 0.7, 0.5, 0.9, 0.6, 1, 0.7, 0.85, 0.55, 0.95, 0.6, 0.8, 0.45, 0.7, 0.4, 0.55, 0.3];

function drawSoundBars(sound) {
    const level = Math.max(0.08, Math.min(1, (sound - 30) / 50));
    $("sound-bars").replaceChildren(...WAVE.map((shape) => {
        const bar = document.createElement("span");
        bar.style.height = `${Math.round(8 + 64 * shape * level)}px`;
        return bar;
    }));
}

function drawReading({ temperature, wet, sound }) {
    $("wet").textContent = wet ? "Wet" : "Dry";
    $("alarm-water").dataset.state = wet ? "on" : "off";
    $("sound").textContent = `${sound} dB`;
    drawSoundBars(sound);

    readings.unshift({ at: Date.now(), temperature, wet, sound });
    readings.length = Math.min(readings.length, CHART_SIZE);
    drawLineChart($("temp-chart"), readings.map((r) => ({ at: r.at, value: r.temperature })).reverse(),
        { label: "Temperature", unit: "°C" });
    drawTemperatureFigures();
    const lines = readings.slice(0, SENSOR_LOG_SIZE).reverse().map((reading) =>
        `${time(reading.at)}  ${reading.temperature} °C · ${reading.wet ? "Wet" : "Dry"} · ${reading.sound} dB`);
    fillLog($("sensor-log"), lines);
}

// ---------------------------------------------------------------- drawing the stored data

const time = (ms) => (ms == null ? "—" : new Date(ms).toLocaleTimeString());

function cell(text, className) {
    const td = document.createElement("td");
    td.textContent = text;
    if (className) td.className = className;
    return td;
}

async function drawIncidents() {
    // Oldest first by start time; added newest first, because the list is a bottom-up frame
    // like the logs: the newest Incident stays in view at the bottom.
    const active = (await store.activeIncidents()).sort((a, b) => a.firstSeen - b.firstSeen);
    // Numbered 1 (oldest) to n (newest), so they are easy to tell apart.
    const items = active.map((incident, i) => {
        const li = document.createElement("li");
        li.className = `incident ${incident.state.toLowerCase()}`;
        const number = Object.assign(document.createElement("span"), { className: "num", textContent: `${i + 1}` });
        li.append(number, `${incident.id} · ${incident.severity} · since ${time(incident.firstSeen)}`);
        return li;
    });
    $("active").replaceChildren(...items.reverse());
    $("active-count").textContent = active.length;
    const warning = active.some((i) => i.state === "Warning");
    const critical = active.some((i) => i.state === "Critical");
    setAlarm("alarm-door", warning, "Warning active");
    setAlarm("alarm-smoke", critical, "Critical active");
    $("active-count").dataset.state = active.some((i) => i.state === "Critical") ? "critical" : active.length ? "warning" : "none";

    const rows = (await store.allIncidents()).map((incident) => {
        const tr = document.createElement("tr");
        tr.append(cell(incident.session), cell(incident.id), cell(incident.severity),
            cell(incident.state, `state ${incident.state.toLowerCase()}`),
            cell(time(incident.firstSeen)), cell(time(incident.updatedAt)), cell(time(incident.closedAt)));
        return tr;
    });
    $("history").replaceChildren(...rows);
}

function setAlarm(id, on, text) {
    $(id).dataset.state = on ? "on" : "off";
    $(id).querySelector(".alarm-state").textContent = on ? text : "Quiet";
}

async function drawLatency() {
    const rows = (await store.latencySummary()).map(({ input, count, median, min, max }) => {
        const tr = document.createElement("tr");
        tr.append(cell(input), cell(count), cell(`${median} µs`), cell(`${min}–${max} µs`));
        return tr;
    });
    $("latency").replaceChildren(...rows);
}

// A log frame shows the newest line at the bottom; older lines move up and out of view and
// stay reachable by scrolling up inside the frame. The frame is laid out bottom-up
// (CSS column-reverse), so the browser keeps it anchored at the newest line by itself.
// `lines` come oldest first; they are added newest first to match that layout.
function fillLog(frame, lines) {
    frame.replaceChildren(...[...lines].reverse().map((text) => Object.assign(document.createElement("li"), { textContent: text })));
}

// One board line as a short sentence for the event log.
function describe(event) {
    switch (event.type) {
        case "hello": return "Board started";
        case "mode": return `Mode: ${event.mode === "NONE" ? "not chosen" : event.mode}`;
        case "event": return `${event.sensor === "smoke" ? "Smoke detected" : "Door opened"} (${event.mode})`;
        case "incident": return `${event.incidentId} ${event.severity.toLowerCase()}: ${event.state}`;
        case "display": return `Screen: ${event.pattern}`;
        case "latency": return `Reaction time, ${event.input}: ${event.us} µs`;
        case "note": return event.message;
        default: return event.type;
    }
}

async function drawEvents() {
    const events = (await store.recentEvents(50)).reverse();
    if (!events.length) return;
    fillLog($("events"), events.map((event) => `${time(event.at)}  ${describe(event)}`));
}

// Incidents per session, Warning vs Critical, for the last 6 sessions that have Incidents.
const SEVERITIES = [
    { key: "WARNING", label: "Warning", className: "warning" },
    { key: "CRITICAL", label: "Critical", className: "critical" },
];

async function drawIncidentChart() {
    const bySession = new Map();
    for (const incident of await store.allIncidents()) {
        const counts = bySession.get(incident.session) ?? { WARNING: 0, CRITICAL: 0 };
        counts[incident.severity] = (counts[incident.severity] ?? 0) + 1;
        bySession.set(incident.session, counts);
    }
    const groups = [...bySession.entries()].sort((a, b) => a[0] - b[0]).slice(-6)
        .map(([s, values]) => ({ label: `#${s}`, values }));
    drawBarChart($("incident-chart"), groups, SEVERITIES, { label: "Incidents per session" });
}

async function drawCounts() {
    const counts = await store.counts();
    $("counts").replaceChildren(...Object.entries(counts).map(([table, n]) =>
        Object.assign(document.createElement("li"), { textContent: `${table}: ${n}` })));
}

async function drawAll() {
    await Promise.all([drawIncidents(), drawIncidentChart(), drawLatency(), drawEvents(), drawCounts()]);
}

// ---------------------------------------------------------------- the board's lines

// The line types our firmware sends (firmware/README.md). Any of them proves the board runs
// Hytte, even if its "hello" was sent a moment before the browser started reading.
const HYTTE_TYPES = new Set(["hello", "mode", "display", "event", "incident", "latency", "note", "reading"]);

board.addEventListener("message", async ({ detail: message }) => {
    $("last-line").textContent = JSON.stringify(message);
    if (HYTTE_TYPES.has(message.type)) {
        clearTimeout(helloTimer);                              // it runs Hytte: all good
        $("not-hytte").hidden = true;
    }
    if (message.type === "hello") {
        session = await store.startSession(message.firmware);   // the board (re)started
        $("session").textContent = `#${session}`;
    }
    if (session == null) {
        session = await store.startSession("unknown");          // connected mid-run, no hello seen
        $("session").textContent = `#${session}`;
    }
    if (message.type === "reading") {
        drawReading(message);   // display only: sensor readings are not stored
        return;
    }
    if (message.type === "mode") drawMode(message.mode);
    if (message.type === "display") drawMatrix(message.pattern);
    await store.recordLine(session, message);
    await drawAll();
});

board.addEventListener("connected", () => {
    setStatus("on", "Connected");
    expectHello();
});
board.addEventListener("disconnected", () => {
    clearTimeout(helloTimer);
    setStatus("off", "Not connected");
    session = null;
});

// Door monitoring only matters in AWAY (Team Guide §6), so its toggle follows the mode.
function drawMode(mode) {
    $("mode").textContent = mode === "NONE" ? "Not chosen" : mode;
    for (const id of ["toggle-away", "toggle-door"]) $(id).classList.toggle("on", mode === "AWAY");
}

function setStatus(state, text) {
    $("status").dataset.state = state;
    $("status").textContent = text;
    $("connect").textContent = state === "on" ? "Disconnect" : "Connect micro:bit";
}

// ---------------------------------------------------------------- buttons

$("connect").addEventListener("click", async () => {
    try {
        if (board.connected) await board.disconnect();
        else await board.connect();
    } catch (error) {
        if (error.name !== "NotFoundError") alert(`Could not connect: ${error.message}`);   // NotFound: picker cancelled
    }
});

// Phones show one log at a time: the tabs switch between the event log and the sensor log.
document.querySelectorAll(".log-tabs button").forEach((tab) => {
    tab.addEventListener("click", () => {
        $("logs").dataset.show = tab.dataset.log;
        document.querySelectorAll(".log-tabs button").forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
        const frame = document.querySelector(`.log-box[data-log="${tab.dataset.log}"] .log-frame`);
        frame.scrollTop = 0;   // bottom-up frame: 0 is the newest line
    });
});

// The "Data" panel: the stored data and tools, over the one-screen dashboard.
$("data-open").addEventListener("click", () => $("data-dialog").showModal());
$("data-close").addEventListener("click", () => $("data-dialog").close());
$("data-dialog").addEventListener("click", (event) => {
    if (event.target === $("data-dialog")) $("data-dialog").close();   // a click on the backdrop
});

$("export").addEventListener("click", async () => {
    const data = await store.exportAll();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    link.download = `hytte-monitoring-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
});

$("import").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    try {
        await store.importAll(JSON.parse(await file.text()));
    } catch (error) {
        alert(error.message);
    }
    event.target.value = "";
    await drawAll();
});

$("sample").addEventListener("click", async () => {
    await store.addSampleData();
    await drawAll();
});

$("clear").addEventListener("click", async () => {
    if (!confirm("Delete every stored session, Incident and event in this browser?")) return;
    await store.clearAll();
    await drawAll();
});

// ---------------------------------------------------------------- start

if (!Board.supported) {
    $("unsupported").hidden = false;
    $("connect").disabled = true;
}
function drawClock() {
    const now = new Date();
    $("clock").textContent = now.toLocaleTimeString();
    $("date").textContent = now.toLocaleDateString([], { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}

drawMatrix("?");
drawLineChart($("temp-chart"), [], { label: "Temperature", unit: "°C" });
drawTemperatureFigures();
drawSoundBars(30);
drawClock();
setInterval(drawClock, 1000);
drawAll();
