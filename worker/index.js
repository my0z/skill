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

// TODO: 실제 앱 값으로 교체
const SCHEME = "beltro";
const STORE = { ios: "https://apps.apple.com/app/idTODO", android: "https://play.google.com/store/apps/details?id=TODO" };

// 앱 열기 시도 후 일정 시간 안에 페이지가 남아 있으면 스토어로 이동
const openPage = (path, ua) => {
  const store = /iphone|ipad|ipod/i.test(ua) ? STORE.ios : STORE.android;
  const app = `${SCHEME}://${path}`;
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Beltro</title></head><body style="font:16px system-ui;text-align:center;padding:4rem 16px"><p>앱을 여는 중입니다</p><a href="${store}">앱 설치하기</a><script>var t=setTimeout(function(){location.href=${JSON.stringify(store)}},1500);document.addEventListener("visibilitychange",function(){if(document.hidden)clearTimeout(t)});location.href=${JSON.stringify(app)}</script></body></html>`;
};

export default {
  async fetch(req) {
    const { pathname } = new URL(req.url);
    if (pathname === "/health") return Response.json({ ok: true });
    if (pathname.startsWith("/open/")) {
      const path = pathname.slice(6).replace(/[^\w\-./]/g, "");
      return new Response(openPage(path, req.headers.get("user-agent") || ""), { headers: { "content-type": "text/html;charset=UTF-8" } });
    }
    if (pathname !== "/") return new Response("Not Found", { status: 404 });
    return new Response(html, { headers: { "content-type": "text/html;charset=UTF-8" } });
  },
};
