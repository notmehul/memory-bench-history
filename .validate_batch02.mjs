import fs from 'fs';
const batch = JSON.parse(fs.readFileSync('/Users/radiohead/Dev/memory-bench/datasets/dev/org-00001/render/batch-02.json', 'utf8'));
const out = JSON.parse(fs.readFileSync('/Users/radiohead/Dev/memory-bench/datasets/dev/org-00001/render/batch-02.out.json', 'utf8'));
const MARKER = /⟦(F-\d{4})⟧([\s\S]*?)⟦\/\1⟧/g;
const EMPH = /(!|\*\*|IMPORTANT|REMINDER|NOTE:)/;
const issues = [];
const batchIds = new Set(batch.events.map(e => e.event_id));
const outIds = new Set(Object.keys(out));
const missing = [...batchIds].filter(id => !outIds.has(id));
const extra = [...outIds].filter(id => !batchIds.has(id));
if (missing.length) issues.push(`missing ${new Set(missing)}`);
if (extra.length) issues.push(`extra ${new Set(extra)}`);
for (const t of batch.events) {
  const eid = t.event_id;
  const text = out[eid];
  const cleaned = text.replace(/⟦F-\d{4}⟧([\s\S]*?)⟦\/F-\d{4}⟧/g, '$1');
  const wc = cleaned.split(/\s+/).filter(Boolean).length;
  const [lo, hi] = t.length_words;
  if (wc < lo || wc > hi) issues.push(`${eid}: wc=${wc} not in [${lo},${hi}]`);
  const found = [...text.matchAll(/⟦(F-\d{4})⟧([\s\S]*?)⟦\/\1⟧/g)].map(m => m[1]);
  const expect = t.embed.map(e => e.fact_id);
  if (JSON.stringify(found) !== JSON.stringify(expect)) issues.push(`${eid}: markers ${found}!=${expect}`);
  const parts = new Set(t.participants.map(p => p.name));
  for (const line of text.split('\n')) {
    if (line.startsWith('-')) continue;
    if (line.includes(':')) {
      const sp = line.split(':', 1)[0];
      if (!parts.has(sp)) issues.push(`${eid}: speaker ${JSON.stringify(sp)} not in ${JSON.stringify([...parts])}`);
    }
  }
  if (text.split('\n')[0].includes('⟦F-')) issues.push(`${eid}: embed first line`);
  for (const m of text.matchAll(/⟦(F-\d{4})⟧([\s\S]*?)⟦\/\1⟧/g)) {
    if (EMPH.test(m[2])) issues.push(`${eid}: emph in ${m[1]}`);
    const caps = m[2].match(/\b[A-Z]{4,}\b/g);
    if (caps) issues.push(`${eid}: CAPS ${caps} in ${m[1]}`);
    const pos = m.index;
    const ls = text.lastIndexOf('\n', pos) + 1;
    let le = text.indexOf('\n', pos);
    if (le < 0) le = text.length;
    const sp = text.slice(ls, le).split(':', 1)[0];
    const exp = t.embed.find(e => e.fact_id === m[1]).speaker;
    if (sp !== exp) issues.push(`${eid}: ${m[1]} by ${sp} want ${exp}`);
    const stmt = t.embed.find(e => e.fact_id === m[1]).statement;
    if (text.includes(stmt)) issues.push(`${eid}: verbatim ${m[1]}`);
  }
  if (t.canary && !text.includes(t.canary)) issues.push(`${eid}: missing canary`);
  console.log(`${eid}: ${wc} words [${lo}-${hi}] embeds=${JSON.stringify(found)}`);
}
console.log(issues.length ? 'ISSUES:' : 'ALL OK');
for (const i of issues) console.log(' ', i);
