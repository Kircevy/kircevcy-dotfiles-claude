#!/usr/bin/env node
import { spawn } from 'child_process';
import { createRequire } from 'module';
import { mkdirSync, existsSync } from 'fs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');

const CHROME_PATH = '/home/wgz/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
const CDP_PORT = 45593;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function findWsUrl() {
  try {
    const resp = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`);
    if (!resp.ok) throw new Error('not ready');
    const info = await resp.json();
    return info.webSocketDebuggerUrl;
  } catch {
    // Also try standard Chrome DevToolsActivePort paths
    const candidates = [
      '/tmp/.com.google.Chrome.DevToolsActivePort',
      '/tmp/playwright-cdp-*/DevToolsActivePort',
      ...(process.env.HOME ? [
        `${process.env.HOME}/.config/google-chrome/DevToolsActivePort`,
        `${process.env.HOME}/.config/chromium/DevToolsActivePort`,
      ] : []),
    ];
    return null;
  }
}

async function ensureChrome() {
  // Check if Chrome already serving CDP
  const existing = await findWsUrl();
  if (existing) return existing;

  // Kill any stale Chrome on our port
  try {
    await fetch(`http://127.0.0.1:${CDP_PORT}/json/close`);
  } catch {}

  // Start new Chrome instance
  const userDataDir = `/tmp/playwright-cdp-${Date.now()}`;
  mkdirSync(userDataDir, { recursive: true });
  const proc = spawn(CHROME_PATH, [
    `--remote-debugging-port=${CDP_PORT}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--headless=new',
    `--user-data-dir=${userDataDir}`,
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-sync',
    '--disable-hang-monitor',
    '--disable-popup-blocking',
    '--no-sandbox',
  ], { detached: true, stdio: 'ignore' });
  proc.unref();

  // Wait for CDP to be ready, up to 15s
  for (let i = 0; i < 30; i++) {
    await sleep(500);
    const url = await findWsUrl();
    if (url) return url;
  }
  throw new Error('Chrome did not start in time');
}

class CDP {
  constructor() { this.id = 0; this.pending = new Map(); }

  async connect(wsUrl) {
    return new Promise((res, rej) => {
      this.ws = new WebSocket(wsUrl);
      this.ws.onopen = () => res();
      this.ws.onerror = () => rej(new Error('WebSocket error'));
      this.ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve, reject } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          if (msg.error) reject(new Error(msg.error.message));
          else resolve(msg.result);
        }
      };
      setTimeout(() => rej(new Error('WS connect timeout')), 10000);
    });
  }

  send(method, params = {}, sessionId) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      const msg = { id, method, params };
      if (sessionId) msg.sessionId = sessionId;
      this.ws.send(JSON.stringify(msg));
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error(`Timeout: ${method}`));
        }
      }, 20000);
    });
  }

  close() { try { this.ws.close(); } catch {} }
}

async function navigateAndGetContent(url) {
  const wsUrl = await ensureChrome();
  const cdp = new CDP();
  await cdp.connect(wsUrl);

  try {
    // Create target tab with URL directly
    const { targetId } = await cdp.send('Target.createTarget', { url });

    // Attach to it
    const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });

    // Wait for page to be reasonably loaded
    await sleep(3000);

    // Also wait for network idle via JS
    await cdp.send('Runtime.evaluate', {
      expression: `new Promise(r => {
        if (document.readyState === 'complete') r();
        else document.addEventListener('readystatechange', () => {
          if (document.readyState === 'complete') r();
        });
      })`,
      awaitPromise: true,
    }, sessionId).catch(() => {});
    await sleep(1000);

    // Get title
    const tRes = await cdp.send('Runtime.evaluate', {
      expression: 'document.title', returnByValue: true,
    }, sessionId);
    const title = tRes.result?.value || '';

    // Get page text
    const txtRes = await cdp.send('Runtime.evaluate', {
      expression: '(document.body?.innerText || "").substring(0, 10000)',
      returnByValue: true,
    }, sessionId);
    const text = txtRes.result?.value || '';

    // Get all visible links (deduplicated, sorted by text length desc for relevance)
    const linksRes = await cdp.send('Runtime.evaluate', {
      expression: `JSON.stringify(
        Array.from(document.querySelectorAll('a[href]'))
          .filter(a => { const s = getComputedStyle(a); return s.display !== 'none' && s.visibility !== 'hidden'; })
          .map(a => ({
            text: (a.textContent || '').replace(/\\s+/g, ' ').trim().substring(0, 100),
            href: a.getAttribute('href') || '',
          }))
          .filter(l => l.href && !l.href.startsWith('javascript:') && !l.href.startsWith('#') && l.text)
          .filter((l, i, arr) => arr.findIndex(x => x.href === l.href) === i)
          .slice(0, 80)
      )`,
      returnByValue: true,
    }, sessionId);
    let links = [];
    try { links = JSON.parse(linksRes.result?.value || '[]'); } catch {}

    // Get nav/sidebar links specifically
    const navRes = await cdp.send('Runtime.evaluate', {
      expression: `JSON.stringify(
        Array.from(document.querySelectorAll('nav a[href], header a[href], [role=navigation] a[href], .sidebar a[href], .menu a[href], .nav a[href], aside a[href], .toc a[href], [class*=nav] a[href], [class*=menu] a[href], [class*=sidebar] a[href], [class*=toc] a[href]'))
          .map(a => ({
            text: (a.textContent || '').replace(/\\s+/g, ' ').trim().substring(0, 100),
            href: a.getAttribute('href') || '',
          }))
          .filter(l => l.href && !l.href.startsWith('javascript:') && !l.href.startsWith('#') && l.text)
          .filter((l, i, arr) => arr.findIndex(x => x.href === l.href) === i)
      )`,
      returnByValue: true,
    }, sessionId);
    let navLinks = [];
    try { navLinks = JSON.parse(navRes.result?.value || '[]'); } catch {}

    // Get headings for structure
    const hRes = await cdp.send('Runtime.evaluate', {
      expression: `JSON.stringify(
        Array.from(document.querySelectorAll('h1, h2, h3'))
          .map(h => ({ level: parseInt(h.tagName[1]), text: (h.textContent || '').trim().substring(0, 80) }))
          .filter(h => h.text)
      )`,
      returnByValue: true,
    }, sessionId);
    let headings = [];
    try { headings = JSON.parse(hRes.result?.value || '[]'); } catch {}

    // Cleanup
    await cdp.send('Target.closeTarget', { targetId }).catch(() => {});
    cdp.close();

    // Deduplicate navLinks from links
    const navHrefs = new Set(navLinks.map(l => l.href));
    const mainLinks = links.filter(l => !navHrefs.has(l.href));

    return { title, text: text.substring(0, 5000), navLinks, mainLinks, headings };
  } catch (e) {
    cdp.close();
    throw e;
  }
}

async function main() {
  const [action, ...args] = process.argv.slice(2);

  if (action === 'open' && args[0]) {
    const result = await navigateAndGetContent(args[0]);
    console.log(JSON.stringify(result));
  } else {
    console.error('Usage: browse.mjs open <url>');
    process.exit(1);
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
