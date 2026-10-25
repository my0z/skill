// 암호화된 금고 한 덩어리만 저장한다. 서버는 내용을 풀 수 없다
const J = (o, s = 200) => new Response(JSON.stringify(o), {status: s, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
const hex = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(x => x.toString(16).padStart(2, '0')).join('');
const okBlob = b => b && ['s', 'i', 'd'].every(k => typeof b[k] === 'string');

export default {
  async fetch(req, env) {
    if (new URL(req.url).pathname !== '/api/vault') return env.ASSETS.fetch(req);
    // 같은 IP 에서 너무 자주 두드리면 막는다 (암호 대입 시도를 늦춘다)
    if (env.RL && !(await env.RL.limit({key: req.headers.get('cf-connecting-ip') || 'x'})).success) return J({e: 'rate'}, 429);
    const tok = (req.headers.get('authorization') || '').replace(/^Bearer /, '');
    if (!/^[0-9a-f]{64}$/.test(tok)) return J({e: 'auth'}, 401);
    const obj = await env.VAULT.get('vault.json');
    const cur = obj && await obj.json();
    if (req.method === 'GET') {
      if (!cur) return J({e: 'none'}, 404);
      if (cur.h !== await hex(tok)) return J({e: 'auth'}, 401);
      return J({v: cur.v, blob: cur.blob});
    }
    if (req.method !== 'PUT') return J({e: 'method'}, 405);
    // 금고를 처음 만들 때는 비밀 설정 키가 필요하다. 만든 뒤에는 같은 암호에서 나온 토큰만 쓸 수 있다
    if (cur ? cur.h !== await hex(tok) : !env.SETUP_KEY || req.headers.get('x-setup') !== env.SETUP_KEY) return J({e: cur ? 'auth' : 'setup'}, cur ? 401 : 403);
    const text = await req.text();
    if (text.length > 9e6) return J({e: 'size'}, 413);
    let b;
    try { b = JSON.parse(text); } catch { return J({e: 'json'}, 400); }
    if (!okBlob(b.blob) || !Number.isInteger(b.base)) return J({e: 'body'}, 400);
    if ((cur ? cur.v : 0) !== b.base) return cur ? J({v: cur.v, blob: cur.blob}, 409) : J({e: 'base'}, 400);
    const v = b.base + 1;
    const put = await env.VAULT.put('vault.json', JSON.stringify({h: cur ? cur.h : await hex(tok), v, blob: {s: b.blob.s, i: b.blob.i, d: b.blob.d}}),
      {onlyIf: cur ? {etagMatches: obj.etag} : {etagDoesNotMatch: '*'}});
    if (!put) return J({e: 'race'}, 503);
    return J({v});
  },
};
