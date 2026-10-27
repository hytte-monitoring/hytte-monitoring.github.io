// The dashboard's two charts, drawn as SVG: a line chart (temperature over the latest readings)
// and a grouped bar chart (Incidents per session). Both have a hover tooltip.
//
// Chart rules followed (dataviz method): one y-axis per chart, 2px lines, 4px rounded bar ends
// on a single baseline, a 2px gap between touching bars, hairline grid, a legend for two series,
// none for one. Series colours come from CSS variables, so dark mode swaps them in one place.

const SVG = "http://www.w3.org/2000/svg";

function svgElement(name, attributes = {}) {
    const element = document.createElementNS(SVG, name);
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
    return element;
}

// One tooltip element shared by every chart on the page.
const tooltip = Object.assign(document.createElement("div"), { className: "chart-tooltip", hidden: true });
document.body.append(tooltip);

function showTooltip(event, lines) {
    tooltip.replaceChildren(...lines.map((text, i) => Object.assign(document.createElement(i ? "span" : "b"), { textContent: text })));
    tooltip.hidden = false;
    const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${event.clientY + 14}px`;
}

function hideTooltip() {
    tooltip.hidden = true;
}

// Round axis steps: 1, 2 or 5 times a power of ten.
function niceStep(range, ticks) {
    const raw = range / ticks;
    const power = 10 ** Math.floor(Math.log10(raw));
    return [1, 2, 5, 10].map((m) => m * power).find((step) => step >= raw);
}

const WIDTH = 640;
const HEIGHT = 240;
const PAD = { top: 12, right: 12, bottom: 28, left: 40 };

function frame(container, empty) {
    const svg = svgElement("svg", { viewBox: `0 0 ${WIDTH} ${HEIGHT}`, class: "chart", role: "img" });
    container.replaceChildren(svg);
    if (empty) {
        const text = svgElement("text", { x: WIDTH / 2, y: HEIGHT / 2, "text-anchor": "middle", class: "chart-empty" });
        text.textContent = empty;
        svg.append(text);
    }
    return svg;
}

function yAxis(svg, min, max, format) {
    const step = niceStep(max - min || 1, 4);
    const low = Math.floor(min / step) * step;
    const high = Math.max(Math.ceil(max / step) * step, low + step);
    const y = (value) => PAD.top + (1 - (value - low) / (high - low)) * (HEIGHT - PAD.top - PAD.bottom);
    for (let value = low; value <= high + step / 2; value += step) {
        svg.append(svgElement("line", { x1: PAD.left, x2: WIDTH - PAD.right, y1: y(value), y2: y(value), class: "chart-grid" }));
        const label = svgElement("text", { x: PAD.left - 8, y: y(value) + 4, "text-anchor": "end", class: "chart-axis" });
        label.textContent = format(value);
        svg.append(label);
    }
    return y;
}

// points: [{ at, value }] oldest first.
export function drawLineChart(container, points, { label, unit }) {
    if (points.length < 2) {
        frame(container, "Connect the micro:bit; the line starts after two readings.");
        return;
    }
    const svg = frame(container);
    svg.setAttribute("aria-label", `${label}: ${points.length} readings, latest ${points.at(-1).value} ${unit}`);
    const values = points.map((p) => p.value);
    const y = yAxis(svg, Math.min(...values) - 1, Math.max(...values) + 1, (v) => `${v}${unit === "°C" ? "°" : ""}`);
    const x = (i) => PAD.left + (i / (points.length - 1)) * (WIDTH - PAD.left - PAD.right);
    const time = (at) => new Date(at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    const path = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
    const baseline = HEIGHT - PAD.bottom;
    svg.append(svgElement("path", { d: `${path} L${x(points.length - 1)},${baseline} L${x(0)},${baseline} Z`, class: "chart-area" }));
    svg.append(svgElement("path", { d: path, class: "chart-line" }));
    const last = points.length - 1;
    svg.append(svgElement("circle", { cx: x(last), cy: y(points[last].value), r: 5, class: "chart-dot" }));

    // Hover: a crosshair and a tooltip at the nearest reading.
    const cross = svgElement("line", { y1: PAD.top, y2: baseline, class: "chart-cross", visibility: "hidden" });
    const marker = svgElement("circle", { r: 5, class: "chart-dot", visibility: "hidden" });
    svg.append(cross, marker);
    const hit = svgElement("rect", { x: PAD.left, y: PAD.top, width: WIDTH - PAD.left - PAD.right, height: baseline - PAD.top, class: "chart-hit" });
    svg.append(hit);
    hit.addEventListener("pointermove", (event) => {
        const box = svg.getBoundingClientRect();
        const svgX = ((event.clientX - box.left) / box.width) * WIDTH;
        const i = Math.max(0, Math.min(last, Math.round(((svgX - PAD.left) / (WIDTH - PAD.left - PAD.right)) * last)));
        for (const element of [cross, marker]) element.setAttribute("visibility", "visible");
        cross.setAttribute("x1", x(i));
        cross.setAttribute("x2", x(i));
        marker.setAttribute("cx", x(i));
        marker.setAttribute("cy", y(points[i].value));
        showTooltip(event, [`${points[i].value} ${unit}`, time(points[i].at)]);
    });
    hit.addEventListener("pointerleave", () => {
        for (const element of [cross, marker]) element.setAttribute("visibility", "hidden");
        hideTooltip();
    });
}

// groups: [{ label, values: { [seriesKey]: number } }]; series: [{ key, label, className }].
export function drawBarChart(container, groups, series, { label }) {
    if (!groups.length) {
        frame(container, "No Incidents stored yet.");
        return;
    }
    const svg = frame(container);
    svg.setAttribute("aria-label", `${label}: ${groups.length} sessions`);
    const max = Math.max(1, ...groups.flatMap((g) => series.map((s) => g.values[s.key] ?? 0)));
    const y = yAxis(svg, 0, max, (v) => `${v}`);
    const slot = (WIDTH - PAD.left - PAD.right) / groups.length;
    const barWidth = Math.min(24, (slot * 0.6 - 2) / series.length);
    const baseline = y(0);

    groups.forEach((group, g) => {
        const groupWidth = series.length * barWidth + (series.length - 1) * 2;
        const start = PAD.left + g * slot + (slot - groupWidth) / 2;
        series.forEach((s, i) => {
            const value = group.values[s.key] ?? 0;
            const left = start + i * (barWidth + 2);
            const top = y(value);
            const height = baseline - top;
            // Rounded top (4px), square at the baseline.
            const r = Math.min(4, height, barWidth / 2);
            const d = height <= 0 ? "" :
                `M${left},${baseline} V${top + r} Q${left},${top} ${left + r},${top} H${left + barWidth - r} ` +
                `Q${left + barWidth},${top} ${left + barWidth},${top + r} V${baseline} Z`;
            const bar = svgElement("path", { d, class: `chart-bar ${s.className}` });
            // A hit area taller than the bar, so short bars are easy to hover.
            const hit = svgElement("rect", { x: left - 1, y: PAD.top, width: barWidth + 2, height: baseline - PAD.top, class: "chart-hit" });
            hit.addEventListener("pointermove", (event) => showTooltip(event, [`${s.label}: ${value}`, group.label]));
            hit.addEventListener("pointerleave", hideTooltip);
            svg.append(bar, hit);
        });
        const tick = svgElement("text", { x: PAD.left + g * slot + slot / 2, y: HEIGHT - 8, "text-anchor": "middle", class: "chart-axis" });
        tick.textContent = group.label;
        svg.append(tick);
    });
}
