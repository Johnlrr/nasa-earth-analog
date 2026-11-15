// slides/deck.html -> slides/SIMILITUDE-slides.pdf + slides/preview/slide-N.png, with layout checks.
// node scripts/slides/render_deck.mjs   (needs Google Chrome; fonts and the QR library load from the web)
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { tmpdir } from 'node:os';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const DECK = join(ROOT, 'slides', 'deck.html');
const PDF = process.env.DECK_PDF || join(ROOT, 'slides', 'SIMILITUDE-slides.pdf');
const PREVIEW = join(ROOT, 'slides', 'preview');
const CHROME = process.env.CHROME || [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].find((p) => existsSync(p));
const PORT = 9350;
const prof = join(tmpdir(), 'similitude-deck-chrome');

const ch = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`,
  '--no-first-run', '--allow-file-access-from-files', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let tabs;
for (let i = 0; i < 60; i++) { try { tabs = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(tabs.find((t) => t.type === 'page').webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r));
let id = 0; const pend = {};
ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } });
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expression) => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: pathToFileURL(DECK).href });
await sleep(1500);
await ev('document.fonts.ready.then(() => true)');
await sleep(1500);

const report = await ev(`(() => {
  const out = { fonts: [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight).slice(0, 8),
    hostLoaded: document.fonts.check('600 40px "Host Grotesk"'), qr: document.documentElement.getAttribute('data-qr'), slides: [] };
  document.querySelectorAll('.slide').forEach((s, i) => {
    const r = s.getBoundingClientRect(); let maxB = 0, maxR = 0; const over = [];
    s.querySelectorAll('*').forEach((el) => {
      const b = el.getBoundingClientRect(); if (!b.width || !b.height) return;
      if (b.bottom > r.bottom - 24 || b.right > r.right - 40) over.push((el.className || el.tagName) + ':' + Math.round(b.bottom - r.top) + 'x' + Math.round(b.right - r.left));
    });
    const imgs = [...s.querySelectorAll('img')].map((im) => ({ src: im.getAttribute('src'), ok: im.complete && im.naturalWidth > 0 }));
    out.slides.push({ n: i + 1, overflow: over.slice(0, 5), imgs });
  });
  return out; })()`);

mkdirSync(PREVIEW, { recursive: true });
const n = report.slides.length;
for (let i = 0; i < n; i++) {
  const top = await ev(`(() => { const s = document.querySelectorAll('.slide')[${i}]; return s.getBoundingClientRect().top + scrollY; })()`);
  const shot = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: top, width: 1920, height: 1080, scale: 0.5 }, captureBeyondViewport: true });
  writeFileSync(join(PREVIEW, `slide-${i + 1}.png`), Buffer.from(shot.result.data, 'base64'));
}
const pdf = await send('Page.printToPDF', { printBackground: true, preferCSSPageSize: true, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 });
writeFileSync(PDF, Buffer.from(pdf.result.data, 'base64'));
console.log(JSON.stringify(report, null, 1));
console.log(`wrote ${PDF} and ${n} previews`);
ws.close(); ch.kill();
try { rmSync(prof, { recursive: true, force: true }); } catch { /* profile still locked: harmless */ }
process.exit(0);
