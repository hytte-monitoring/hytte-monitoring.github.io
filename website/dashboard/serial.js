// The micro:bit on the other end of a WebSerial port. The board sends one JSON object per
// line (firmware/README.md); this class fires a "message" event per line (detail: the parsed
// object), and "connected" / "disconnected" events.
//
// Adapted from demos/microbit-library/dashboard/board.js in aiunderstand/ModelDrivenDesign_ex2
// (commit d439b1a). Our firmware only sends, so there are no commands to the board.

const MICROBIT_USB_VENDOR = 0x0d28;   // Arm DAPLink, the micro:bit's USB interface chip

export class Board extends EventTarget {
    #port = null;
    #reader = null;
    #closed = null;

    static get supported() {
        return "serial" in navigator;
    }

    get connected() {
        return this.#port != null;
    }

    async connect() {
        const port = await navigator.serial.requestPort({ filters: [{ usbVendorId: MICROBIT_USB_VENDOR }] });
        await port.open({ baudRate: 115200 });
        this.#port = port;
        navigator.serial.addEventListener("disconnect", this.#onUnplug);
        this.#closed = this.#readLines(port);
        this.dispatchEvent(new Event("connected"));
    }

    async disconnect() {
        const port = this.#port;
        if (!port) return;
        this.#port = null;
        navigator.serial.removeEventListener("disconnect", this.#onUnplug);
        try { await this.#reader?.cancel(); } catch { /* already gone */ }
        await this.#closed;
        try { await port.close(); } catch { /* unplugged */ }
        this.dispatchEvent(new Event("disconnected"));
    }

    #onUnplug = (event) => {
        if (event.target === this.#port) this.disconnect();
    };

    async #readLines(port) {
        const decoder = new TextDecoderStream();
        const piped = port.readable.pipeTo(decoder.writable).catch(() => {});
        this.#reader = decoder.readable.getReader();
        let buffer = "";
        try {
            for (;;) {
                const { value, done } = await this.#reader.read();
                if (done) break;
                buffer += value;
                let end;
                while ((end = buffer.indexOf("\n")) >= 0) {
                    const line = buffer.slice(0, end).trim();
                    buffer = buffer.slice(end + 1);
                    if (line) this.#handle(line);
                }
            }
        } catch {
            // the port went away; disconnect() tidies up
        } finally {
            this.#reader.releaseLock();
            this.#reader = null;
        }
        await piped;
        if (this.#port === port) this.disconnect();
    }

    #handle(line) {
        let message;
        try {
            message = JSON.parse(line);
        } catch {
            return;   // half a line from before the port opened
        }
        this.dispatchEvent(new CustomEvent("message", { detail: message }));
    }
}
