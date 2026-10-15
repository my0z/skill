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

const tag = (s, t) =>
  s.match(new RegExp(`<${t}[^>]*>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?</${t}>`))?.[1].trim();

// shortcut: RSS 2.0 only and no Atom — upgrade when a feed needs it
export async function collect(env) {
  for (const url of (env.FEEDS ?? "").split(/\s+/).filter(Boolean)) {
    try {
      const xml = await (await fetch(url)).text();
      for (const item of xml.match(/<item\b[\s\S]*?<\/item>/g) ?? []) {
        const link = tag(item, "link");
        const title = tag(item, "title");
        if (!link || !title) continue;
        const r = await env.DB.prepare("INSERT OR IGNORE INTO items(link,title) VALUES(?,?)").bind(link, title).run();
        if (r.meta.changes) await env.JOBS.send({ link, title });
      }
    } catch (e) {
      console.error("feed failed", url, e);
    }
  }
}

export default {
  async scheduled(_, env, ctx) {
    ctx.waitUntil(collect(env));
  },
  async fetch(req) {
    const { pathname } = new URL(req.url);
    if (pathname === "/health") return Response.json({ ok: true });
    if (pathname !== "/") return new Response("Not Found", { status: 404 });
    return new Response(html, { headers: { "content-type": "text/html;charset=UTF-8" } });
  },
};
