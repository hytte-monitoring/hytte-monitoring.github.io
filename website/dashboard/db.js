// The dashboard's database: IndexedDB in the browser, through Dexie (spec §6).
//
//   sessions   one row per board start ("hello")            { id, startedAt, firmware }
//   incidents  one row per Incident, UPDATED IN PLACE        { key, session, id, severity, state,
//              (Team Guide §9: the same history record)        firstSeen, updatedAt, closedAt }
//   events     every line the board sent, append only        { id, at, session, type, ...fields }
//
// The board restarts its ids at I-1 after a reset, so an Incident's key is "session/id".
// Every column is a plain value, so the tables can be imported into SQL (DoltHub) unchanged.
// Times are milliseconds since 1970 (Date.now()).
import Dexie from "https://cdn.jsdelivr.net/npm/dexie@4.4.6/dist/dexie.mjs";

export const db = new Dexie("hytte-monitoring");
db.version(1).stores({
    sessions: "++id, startedAt",
    incidents: "key, session, state, updatedAt",
    events: "++id, at, session, type",
});

export const TABLES = ["sessions", "incidents", "events"];

export async function startSession(firmware, at = Date.now()) {
    return db.sessions.add({ startedAt: at, firmware });
}

export async function latestSession() {
    return db.sessions.orderBy("startedAt").last();
}

// One line from the board: always logged as an event; an "incident" line also creates or
// updates that Incident's row.
export async function recordLine(session, message, at = Date.now()) {
    // An incident line's "id" is the Incident's id, not the event's own key: keep it apart.
    const { type, id: incidentId, ...fields } = message;
    await db.transaction("rw", db.events, db.incidents, async () => {
        await db.events.add({ at, session, type, ...fields, ...(incidentId ? { incidentId } : {}) });
        if (type !== "incident") return;
        const key = `${session}/${message.id}`;
        const existing = await db.incidents.get(key);
        const closedAt = message.state === "Closed" ? at : null;
        if (existing) {
            await db.incidents.update(key, { state: message.state, severity: message.severity, updatedAt: at, closedAt });
        } else {
            await db.incidents.add({
                key, session, id: message.id, severity: message.severity, state: message.state,
                firstSeen: at, updatedAt: at, closedAt,
            });
        }
    });
}

export async function allIncidents() {
    return db.incidents.orderBy("updatedAt").reverse().toArray();
}

export async function activeIncidents() {
    return db.incidents.filter((incident) => incident.state === "Warning" || incident.state === "Critical").toArray();
}

export async function recentEvents(limit = 50) {
    return db.events.orderBy("id").reverse().limit(limit).toArray();
}

// Median on-board latency per input, from the board's "latency" lines.
export async function latencySummary() {
    const byInput = {};
    await db.events.where("type").equals("latency").each((event) => {
        (byInput[event.input] ??= []).push(event.us);
    });
    return Object.entries(byInput).map(([input, values]) => {
        const sorted = [...values].sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);
        const median = sorted.length % 2 ? sorted[middle] : Math.round((sorted[middle - 1] + sorted[middle]) / 2);
        return { input, count: sorted.length, median, min: sorted[0], max: sorted[sorted.length - 1] };
    });
}

// ---------------------------------------------------------------- the database panel

export async function counts() {
    const result = {};
    for (const table of TABLES) result[table] = await db.table(table).count();
    return result;
}

export async function exportAll() {
    const data = { format: "hytte-monitoring", version: 1, exportedAt: new Date().toISOString() };
    for (const table of TABLES) data[table] = await db.table(table).toArray();
    return data;
}

export async function importAll(data) {
    if (data?.format !== "hytte-monitoring") throw new Error("This is not a hytte-monitoring export.");
    await db.transaction("rw", TABLES.map((table) => db.table(table)), async () => {
        for (const table of TABLES) {
            await db.table(table).clear();
            await db.table(table).bulkAdd(data[table] ?? []);
        }
    });
}

export async function clearAll() {
    await db.transaction("rw", TABLES.map((table) => db.table(table)), async () => {
        for (const table of TABLES) await db.table(table).clear();
    });
}

// A short made-up session in the board's own format, for trying the page without a board.
export async function addSampleData(now = Date.now()) {
    const session = await startSession("sample", now - 600_000);
    const lines = [
        { type: "mode", mode: "HOME" },
        { type: "mode", mode: "AWAY" },
        { type: "event", sensor: "door", mode: "AWAY" },
        { type: "incident", id: "I-1", severity: "WARNING", state: "Warning" },
        { type: "latency", input: "door", us: 82 },
        { type: "event", sensor: "smoke", mode: "AWAY" },
        { type: "incident", id: "I-2", severity: "CRITICAL", state: "Critical" },
        { type: "latency", input: "smoke", us: 112 },
        { type: "incident", id: "I-2", severity: "CRITICAL", state: "Closed" },
        { type: "latency", input: "resolve", us: 28 },
    ];
    for (const [i, line] of lines.entries()) await recordLine(session, line, now - 600_000 + i * 30_000);
}
