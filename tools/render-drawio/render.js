#!/usr/bin/env node
/*
 * Render .drawio files to PNG, exactly as draw.io draws them.
 *
 *   node tools/render-drawio/render.js <file.drawio>... [--page N] [--out DIR] [--scale S]
 *
 * Every page is rendered unless --page is given (0-based). PNGs go to
 * .cache/drawio-renders/ unless --out is given; their paths are printed, one per line.
 *
 * Uses draw.io's own viewer (viewer-static.min.js, downloaded once into
 * .cache/drawio-viewer/) in headless Chromium via puppeteer. Set up once with:
 *
 *   npm install --prefix tools/render-drawio
 */
const fs = require("fs");
const path = require("path");

const REPO = path.resolve(__dirname, "..", "..");
const VIEWER_URL = "https://viewer.diagrams.net/js/viewer-static.min.js";
const VIEWER = path.join(REPO, ".cache", "drawio-viewer", "viewer-static.min.js");

function usage(message) {
  if (message) console.error(`render-drawio: ${message}`);
  console.error("usage: node tools/render-drawio/render.js <file.drawio>... [--page N] [--out DIR] [--scale S]");
  process.exit(2);
}

function parseArgs(argv) {
  const opts = { files: [], page: null, out: path.join(REPO, ".cache", "drawio-renders"), scale: 1 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--page") opts.page = parseInt(argv[++i], 10);
    else if (a === "--out") opts.out = path.resolve(argv[++i]);
    else if (a === "--scale") opts.scale = parseFloat(argv[++i]);
    else if (a === "-h" || a === "--help") usage();
    else if (a.startsWith("--")) usage(`unknown option ${a}`);
    else opts.files.push(path.resolve(a));
  }
  if (!opts.files.length) usage("no .drawio file given");
  return opts;
}

async function viewerScript() {
  if (!fs.existsSync(VIEWER)) {
    const res = await fetch(VIEWER_URL);
    if (!res.ok) throw new Error(`could not download the draw.io viewer: HTTP ${res.status}`);
    fs.mkdirSync(path.dirname(VIEWER), { recursive: true });
    fs.writeFileSync(VIEWER, Buffer.from(await res.arrayBuffer()));
  }
  return VIEWER;
}

function pageNames(xml) {
  const names = [...xml.matchAll(/<diagram\b[^>]*?\bname="([^"]*)"/g)].map((m) => m[1]);
  return names.length ? names : ["page"];
}

function slug(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "page";
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  let puppeteer;
  try {
    puppeteer = require("puppeteer");
  } catch {
    usage("puppeteer is not installed. Run once: npm install --prefix tools/render-drawio");
  }
  const viewer = await viewerScript();
  fs.mkdirSync(opts.out, { recursive: true });

  const browser = await puppeteer.launch({ headless: true });
  try {
    for (const file of opts.files) {
      const xml = fs.readFileSync(file, "utf8");
      const names = pageNames(xml);
      const pages = opts.page === null ? names.map((_, i) => i) : [opts.page];
      for (const index of pages) {
        if (index < 0 || index >= names.length) usage(`${path.basename(file)} has no page ${index}`);
        const tab = await browser.newPage();
        await tab.setViewport({ width: 2400, height: 1600, deviceScaleFactor: opts.scale });
        await tab.setContent('<html><body style="margin:0;background:#fff"></body></html>');
        await tab.addScriptTag({ path: viewer });
        await tab.evaluate((xml, index) => {
          const div = document.createElement("div");
          div.className = "mxgraph";
          div.setAttribute("data-mxgraph", JSON.stringify({
            xml, page: index, toolbar: "", nav: false, resize: true, border: 10, lightbox: false,
          }));
          document.body.appendChild(div);
          GraphViewer.processElements();
        }, xml, index);
        await tab.waitForSelector(".mxgraph svg", { timeout: 20000 });
        await new Promise((r) => setTimeout(r, 1000));   // let fonts and markers settle
        const stem = path.basename(file).replace(/\.drawio$/, "");
        const out = path.join(opts.out, `${stem}-p${index + 1}-${slug(names[index])}.png`);
        await (await tab.$(".mxgraph")).screenshot({ path: out });
        await tab.close();
        console.log(out);
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(`render-drawio: ${err.message}`);
  process.exit(1);
});
