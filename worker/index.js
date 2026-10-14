const icon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#E1306C"/><rect y="25" width="64" height="14" fill="#FFD54A"/><rect x="18" y="16" width="28" height="32" rx="5" fill="none" stroke="#fff" stroke-width="5"/><rect x="29" y="22" width="6" height="20" rx="3" fill="#fff"/></svg>`;

// shortcut: 검색 링크라 수익 추적 없음, 파트너스 API 키 생기면 딥링크로 교체
const link = (q) => `https://www.coupang.com/np/search?q=${encodeURIComponent(q)}`;

const belts = [
  ["가죽 벨트", "남성 가죽 벨트"],
  ["자동 벨트", "자동 벨트 버클"],
  ["캔버스 벨트", "캔버스 벨트"],
  ["골프 벨트", "골프 벨트"],
  ["여성 벨트", "여성 벨트"],
];

const cards = belts
  .map(([name, q]) => `<a class="card" href="${link(q)}" target="_blank" rel="sponsored noopener">${icon}<b>${name}</b><small>쿠팡에서 보기</small></a>`)
  .join("");

const html = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Beltro</title>
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<style>
:root{--bg:#fff;--fg:#111;--mute:#666;--accent:#E1306C;--card:#f5f5f7}
@media(prefers-color-scheme:dark){:root{--bg:#0e0e10;--fg:#f2f2f2;--mute:#999;--card:#1b1b1f}}
*{box-sizing:border-box}
body{margin:0;padding:48px 16px;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}
main{max-width:520px;margin:0 auto;text-align:center}
h1{font-size:clamp(2.5rem,10vw,4rem);margin:0 0 .25rem;letter-spacing:-.03em}
h1 span{color:var(--accent)}
p{color:var(--mute);margin:0 0 1.5rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:20px 12px;background:var(--card);border-radius:16px;color:var(--fg);text-decoration:none}
.card svg{width:64px;height:64px}
.card small{color:var(--mute)}
footer{margin-top:2rem;font-size:.75rem;color:var(--mute)}
</style>
</head>
<body>
<main>
<h1>Bel<span>tro</span></h1>
<p>벨트는 허리에 매는 겁니다</p>
<div class="grid">${cards}</div>
<footer>이 페이지는 쿠팡 파트너스 활동의 일환으로 이에 따른 일정액의 수수료를 제공받을 수 있습니다.</footer>
</main>
</body>
</html>`;

export default {
  async fetch(req) {
    const { pathname } = new URL(req.url);
    if (pathname === "/health") return Response.json({ ok: true });
    if (pathname === "/icon.svg") return new Response(icon, { headers: { "content-type": "image/svg+xml" } });
    if (pathname !== "/") return new Response("Not Found", { status: 404 });
    return new Response(html, { headers: { "content-type": "text/html;charset=UTF-8" } });
  },
};
