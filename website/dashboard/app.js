// The dashboard page: connects the board (serial.js) to the database (db.js) and draws them.
import { Board } from "./serial.js";
import * as store from "./db.js";

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

// The last readings, in this page's memory only: not stored, gone after a reload.
const SENSOR_LOG_SIZE = 20;
const sensorLog = [];

function drawReading({ temperature, wet, sound }) {
    $("temperature").textContent = `${temperature} °C`;
    $("wet").textContent = wet ? "Wet (logo touched)" : "Dry";
    $("wet").dataset.state = wet ? "wet" : "dry";
    $("sound").textContent = `${sound} dB`;

    sensorLog.unshift({ at: Date.now(), temperature, wet, sound });
    sensorLog.length = Math.min(sensorLog.length, SENSOR_LOG_SIZE);
    $("sensor-log").replaceChildren(...sensorLog.map((reading) => {
        const tr = document.createElement("tr");
        tr.append(cell(new Date(reading.at).toLocaleTimeString()), cell(`${reading.temperature} °C`),
            cell(reading.wet ? "Wet" : "Dry", reading.wet ? "wet" : ""), cell(`${reading.sound} dB`));
        return tr;
    }));
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
    const active = await store.activeIncidents();
    $("active").replaceChildren(...(active.length ? active.map((incident) => {
        const li = document.createElement("li");
        li.className = `incident ${incident.state.toLowerCase()}`;
        li.textContent = `${incident.id} · ${incident.severity} · since ${time(incident.firstSeen)}`;
        return li;
    }) : [Object.assign(document.createElement("li"), { className: "empty", textContent: "No active Incidents." })]));

    const rows = (await store.allIncidents()).map((incident) => {
        const tr = document.createElement("tr");
        tr.append(cell(incident.session), cell(incident.id), cell(incident.severity),
            cell(incident.state, `state ${incident.state.toLowerCase()}`),
            cell(time(incident.firstSeen)), cell(time(incident.updatedAt)), cell(time(incident.closedAt)));
        return tr;
    });
    $("history").replaceChildren(...rows);
}

async function drawLatency() {
    const rows = (await store.latencySummary()).map(({ input, count, median, min, max }) => {
        const tr = document.createElement("tr");
        tr.append(cell(input), cell(count), cell(`${median} µs`), cell(`${min}–${max} µs`));
        return tr;
    });
    $("latency").replaceChildren(...rows);
}

async function drawEvents() {
    const events = await store.recentEvents(50);
    $("events").replaceChildren(...events.map(({ id, at, session: s, ...fields }) => {
        const li = document.createElement("li");
        li.textContent = `${time(at)}  #${s}  ${JSON.stringify(fields)}`;
        return li;
    }));
}

async function drawCounts() {
    const counts = await store.counts();
    $("counts").replaceChildren(...Object.entries(counts).map(([table, n]) =>
        Object.assign(document.createElement("li"), { textContent: `${table}: ${n}` })));
}

async function drawAll() {
    await Promise.all([drawIncidents(), drawLatency(), drawEvents(), drawCounts()]);
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
    if (message.type === "mode") $("mode").textContent = message.mode;
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
drawMatrix("?");
drawAll();
