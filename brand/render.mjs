// icon.html 시안을 brand/sell-usb-<v>.png 로 찍는다 · node brand/render.mjs [미리보기.png]
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const dir = fileURLToPath(new URL('.', import.meta.url));
const names = { c: 'c-tag', d: 'd-bag', e: 'e-play', f: 'f-sticker' };
const b = await chromium.launch();
const pg = await b.newPage({ viewport: { width: 1080, height: 1080 } });
for (const [v, n] of Object.entries(names)) {
  await pg.goto(`file://${dir}icon.html?v=${v}`, { waitUntil: 'networkidle' });
  await pg.evaluate(() => document.fonts.ready);
  await pg.screenshot({ path: `${dir}sell-usb-${n}.png` });
}
// 미리보기: 동그랗게 자른 모습 (큰 것 + 100px + 48px)
const out = process.argv[2];
if (out) {
  const imgs = Object.values(names).map(n => 'data:image/png;base64,' + readFileSync(`${dir}sell-usb-${n}.png`).toString('base64'));
  const row = (src, i) => `<div><b>${i + 1}</b>${[300, 100, 48].map(s => `<img src="${src}" width="${s}" height="${s}">`).join('')}</div>`;
  await pg.setViewportSize({ width: 1000, height: 1400 });
  await pg.setContent(`<style>body{margin:0;background:#fff;font:700 40px sans-serif}div{display:flex;align-items:center;gap:40px;padding:20px 40px}img{border-radius:50%}</style>${imgs.map(row).join('')}`);
  await pg.screenshot({ path: out, fullPage: true });
}
await b.close();
