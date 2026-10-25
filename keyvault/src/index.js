// 암호화된 금고 한 덩어리와 이전 버전 몇 개만 저장한다. 서버는 내용을 풀 수 없다
const J = (o, s = 200) => new Response(JSON.stringify(o), {status: s, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
const hex = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(x => x.toString(16).padStart(2, '0')).join('');
const okBlob = b => b && ['s', 'i', 'd'].every(k => typeof b[k] === 'string');
const TOK = /^[0-9a-f]{64}$/;
// 이전 버전: 마지막 보관 후 5분이 지났거나 요청이 강제하면 덮어쓰기 직전 상태를 남기고 최근 50개만 둔다
const KEEP = 50, GAP = 5 * 60e3;
// 강제 보관 요청도 이 간격 안에서는 한 번만 받는다 (토큰만 가진 쪽이 이력을 밀어내는 것을 늦춘다)
const hkey = (v, t) => `history/${String(v).padStart(8, '0')}-${t}.json`;
const parse = k => { const m = /^history\/(\d+)-(\d+)\.json$/.exec(k); return m && {v: +m[1], t: +m[2], key: k}; };
async function hist(env) {
  const out = [];
  let cursor;
  do {
    const r = await env.VAULT.list({prefix: 'history/', cursor});
    out.push(...r.objects.map(o => parse(o.key)).filter(Boolean));
    cursor = r.truncated ? r.cursor : undefined;
  } while (cursor);
  return out.sort((a, b) => a.v - b.v || a.t - b.t);
}

export default {
  async fetch(req, env) {
    const path = new URL(req.url).pathname;
    if (path !== '/api/vault' && path !== '/api/history') return env.ASSETS.fetch(req);
    // 같은 IP 에서 너무 자주 두드리면 막는다 (암호 대입 시도를 늦춘다)
    if (env.RL && !(await env.RL.limit({key: req.headers.get('cf-connecting-ip') || 'x'})).success) return J({e: 'rate'}, 429);
    const tok = (req.headers.get('authorization') || '').replace(/^Bearer /, '');
    if (!TOK.test(tok)) return J({e: 'auth'}, 401);
    const obj = await env.VAULT.get('vault.json');
    const cur = obj && await obj.json();

    if (path === '/api/history') {
      if (req.method !== 'GET') return J({e: 'method'}, 405);
      if (!cur) return J({e: 'none'}, 404);
      if (cur.h !== await hex(tok)) return J({e: 'auth'}, 401);
      const list = await hist(env), v = new URL(req.url).searchParams.get('v');
      if (v === null) return J({list: list.map(({v, t}) => ({v, t})).reverse()});
      const hit = list.filter(x => x.v === +v).at(-1);
      const o = hit && await env.VAULT.get(hit.key);
      return o ? J(await o.json()) : J({e: 'none'}, 404);
    }

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
    if (!okBlob(b.blob) || !Number.isInteger(b.base) || (b.newauth !== undefined && !TOK.test(b.newauth))) return J({e: 'body'}, 400);
    if ((cur ? cur.v : 0) !== b.base) return cur ? J({v: cur.v, blob: cur.blob}, 409) : J({e: 'base'}, 400);
    const v = b.base + 1;
    const next = {h: b.newauth ? await hex(b.newauth) : cur ? cur.h : await hex(tok), v, blob: {s: b.blob.s, i: b.blob.i, d: b.blob.d}};
    const put = await env.VAULT.put('vault.json', JSON.stringify(next), {onlyIf: cur ? {etagMatches: obj.etag} : {etagDoesNotMatch: '*'}});
    if (!put) return J({e: 'race'}, 503);
    if (cur) {
      let list = await hist(env);
      if (b.newauth) { // 암호를 바꾸면 이전 버전은 옛 키로 잠겨 있어 쓸 수 없으므로 지운다
        if (list.length) await env.VAULT.delete(list.map(x => x.key));
      } else {
        const last = list.at(-1);
        if (!last || Date.now() - last.t > GAP || b.snap === true && Date.now() - last.t >= Number(env.SNAP_MIN ?? 30e3)) {
          const t = Date.now();
          await env.VAULT.put(hkey(cur.v, t), JSON.stringify({v: cur.v, t, blob: cur.blob}));
          list = await hist(env);
          if (list.length > KEEP) await env.VAULT.delete(list.slice(0, list.length - KEEP).map(x => x.key));
        }
      }
    }
    return J({v});
  },
};
