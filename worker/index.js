const html = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Beltro</title>
<style>
:root{--bg:#fff;--fg:#111;--mute:#666;--accent:#f6821f}
@media(prefers-color-scheme:dark){:root{--bg:#0e0e10;--fg:#f2f2f2;--mute:#999}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;padding:0 16px;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}
main{max-width:520px;text-align:center}
h1{font-size:clamp(2.5rem,10vw,4rem);margin:0 0 .5rem;letter-spacing:-.03em}
h1 span{color:var(--accent)}
p{color:var(--mute);margin:0 0 2rem}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid currentColor}
</style>
</head>
<body>
<main>
<h1>Bel<span>tro</span></h1>
<p>페이지 준비 중입니다. 곧 찾아뵙겠습니다.</p>
<a href="/health">상태 확인</a>
</main>
</body>
</html>`;

export default {
  async fetch(req) {
    const { pathname } = new URL(req.url);
    if (pathname === "/health") return Response.json({ ok: true });
    if (pathname !== "/") return new Response("Not Found", { status: 404 });
    return new Response(html, { headers: { "content-type": "text/html;charset=UTF-8" } });
  },
};
