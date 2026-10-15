import test from "node:test";
import assert from "node:assert/strict";
import { collect } from "./index.js";

test("새 항목만 큐에 넣는다", async () => {
  globalThis.fetch = async () => ({
    text: async () => `<rss><channel>
      <item><title><![CDATA[A]]></title><link>https://x/a</link></item>
      <item><title>B</title><link>https://x/b</link></item>
      <item><title>A again</title><link>https://x/a</link></item>
    </channel></rss>`,
  });
  const seen = new Set();
  const sent = [];
  const env = {
    FEEDS: "https://feed",
    DB: { prepare: () => ({ bind: (link) => ({ run: async () => ({ meta: { changes: seen.has(link) ? 0 : (seen.add(link), 1) } }) }) }) },
    JOBS: { send: async (m) => sent.push(m) },
  };
  await collect(env);
  assert.deepEqual(sent, [{ link: "https://x/a", title: "A" }, { link: "https://x/b", title: "B" }]);
});
