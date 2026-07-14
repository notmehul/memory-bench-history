import { readFileSync } from 'fs';

const batch = JSON.parse(readFileSync('datasets/dev/org-00002-twin/render/batch-01.json', 'utf8'));

const P = {
  'F-0010': 'Sev-1 postmortems company-wide can bypass the five-whys template when the cause is already known',
  'F-0013': 'The company kept a deploy freeze going through the Black Friday traffic peak',
  'F-0015': 'Growth Sev-2 writeups might drop timelines when writers are double-booked',
  'F-0016': 'Partner escalations may wait until the following business day for acknowledgment through the shared support alias',
  'F-0021': 'Partner escalations might wait forty-five minutes when juniors alone are staffing',
  'F-0031': 'Company services may keep shipping features after fully draining the monthly error budget',
  'F-0037': 'Quarterly capacity plans may leave out any contingency buffer when headcount stays stable',
  'F-0042': 'Quarterly capacity plans might apply a five-percent buffer while hiring is frozen',
  'F-0051': 'Feature flags company-wide may remain temporary indefinitely without a retirement date',
  'F-0054': 'The latest infra hire completed a four-interview loop in eight business days',
  'F-0057': 'Company runbooks require a review only after a related Sev-1 incident',
  'F-0077': 'Growth launches may finish checklist sign-off after go-live with no penalty',
  'F-0096': 'Growth Sev-2 writeups might postpone experiment impact numbers when analysts are offline',
  'F-0097': 'Growth permits unlimited unfinished stories rolling into the next sprint',
  'F-0111': 'Feature flags company-wide may remain temporary lacking any retirement deadline after creation',
  'F-0114': "Eighteen production access requests got cleared by infra during last week's incident surge",
  'F-0116': 'Feature flags company-wide might stay temporary for ninety days when owners are understaffed',
  'F-0117': 'Growth may skip design docs for any changes estimated in engineer-day size',
  'F-0120': 'Growth held office hours drawing twenty-two attendees across four sessions last month',
  'F-0043': 'Growth can revise quarterly list prices at any time via a Slack note',
  'F-0086': 'Schema migrations on infra require a written rollback note before merge',
  'F-0103': 'Production releases from infra ship only on the last Friday each month',
  'F-0092': 'Growth Sev-2 postmortems can skip experiment impact figures for internal-only incidents',
  'F-0112': 'Experiment flags on Growth may stay active for ninety days after experiment end',
  'F-0113': 'Marco prefers to keep his personal flags live for thirty days after rollout',
  'F-0073': 'Priya prefers to file security review tickets the week after launch',
  'F-0001': 'Growth ships production releases only once monthly on the last Friday',
  'F-0022': 'Vendor invoices for infra under fifteen thousand dollars may be paid without finance review',
  'F-0047': 'Production database migrations on infra may merge with a single self-approval',
  'F-0087': 'Webhook path segments for Growth may use singular camelCase nouns',
  'F-0033': 'Lena prefers to ship through her full personal error budget before pausing launches',
  'F-0005': 'Standups on Growth run for forty-five minutes covering full ticket-by-ticket status',
  'F-0017': 'Escalations from partners may wait two business days for acknowledgment via the shared support alias',
  'F-0019': 'Slack response targets for Growth are posted under Comms in the team handbook',
  'F-0038': 'Capacity plans each quarter may drop contingency buffers during hiring freezes',
  'F-0060': 'Brand voice examples company-wide are linked under Voice in the marketing handbook',
  'F-0071': 'Customer-data features company-wide may skip security review before production launch',
  'F-0078': 'Launches on Growth may finish checklist sign-off the morning of go-live',
  'F-0091': 'Sev-1 postmortems company-wide may omit customer segment lists when leadership already knows',
  'F-0098': 'Growth allows five unfinished stories to keep rolling into the next sprint',
  'F-0122': 'Growth might waive design docs above five engineer-days when architects stay offline',
  'F-0026': 'Bug triage on infra is handled ad hoc by whoever files the first comment',
  'F-0011': 'Sev-2 postmortems on Growth may omit the customer-impact timeline for internal-only outages',
  'F-0032': 'Growth may keep shipping out experiments after fully exhausting the team error budget',
  'F-0072': 'Payment changes on Growth may skip security review until after production launch',
  'F-0012': 'Marco prefers drafting postmortems as polished narrative prose before any outline',
  'F-0045': 'Priya prefers to pay infra on-call as a flat weekly stipend',
  'F-0052': 'Experiment flags on Growth may stay active for six months after experiment end',
  'F-0107': 'Support on Growth must get manager approval for every refund above ten dollars',
  'F-0067': 'Infra allows unlimited sprint carryover so long as tickets remain assigned',
  'F-0053': 'Lena prefers to keep her personal flags live for at least sixty days after rollout',
  'F-0063': 'Growth public API paths rely on camelCase resource names',
  'F-0083': 'Schema migrations on Growth may merge without any written rollback note',
  'F-0034': 'Diego prefers to end Friday pager handoffs with a three-bullet Loom summary',
  'F-0058': 'Runbooks company-wide need review only during annual compliance audits',
  'F-0074': 'On-call escalation steps for infra are summarized under Escalation in the ops wiki',
  'F-0094': 'Anouk prefers to pause her experiments at forty percent team error-budget burn',
  'F-0102': 'Growth might allow four unfinished stories to keep rolling when the sprint is understaffed',
  'F-0118': 'Growth can omit design docs unless a change exceeds eight engineer-days',
  'F-0093': 'Felix prefers to assign postmortem action owners only after the final write-up',
  'F-0018': 'Escalations from partners may wait until weekly partner sync for acknowledgment via the shared support alias',
  'F-0036': 'Growth might freeze experiments only after fully exhausting the team error budget',
  'F-0039': 'Capacity plans each quarter may book teams at one-hundred-percent utilization with no buffer',
  'F-0040': 'Wren prefers to keep new services above eighty percent unit test coverage',
  'F-0059': 'Runbooks company-wide need no scheduled review once published',
  'F-0079': 'Launches on Growth may skip checklist sign-off for dark flag-only ships',
  'F-0080': 'Quarterly pricing sheets for Growth are stored under Pricing in the finance drive',
  'F-0099': 'Growth allows every unfinished story rolling into the next sprint unchecked',
  'F-0100': 'Two vendor contracts were closed by infra after four redline rounds last quarter',
  'F-0119': 'Growth may skip design docs for every multi-service change under a flag',
};

const HEDGE = /\b(i think|i believe|for what it's worth|maybe|probably|sort of|kind of|arguably)\b/i;

function normalize(s) {
  return s.toLowerCase().trim().replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim();
}

function nearVerbatimKind(stmt, paraphrase) {
  const na = normalize(stmt);
  const nb = normalize(paraphrase);
  const wa = na.split(/\s+/).filter(Boolean);
  const wb = nb.split(/\s+/).filter(Boolean);
  if (na === nb) return 'exact_match';
  if (wa.length === wb.length) {
    const diffs = wa.map((a, i) => (a !== wb[i] ? i : -1)).filter((i) => i >= 0);
    if (diffs.length === 1) return 'one_word_swap';
  }
  if (Math.abs(wa.length - wb.length) === 1) {
    const longer = wa.length > wb.length ? wa : wb;
    const shorter = wa.length > wb.length ? wb : wa;
    for (let i = 0; i < longer.length; i++) {
      if (longer.slice(0, i).concat(longer.slice(i + 1)).join(' ') === shorter.join(' ')) {
        return 'one_word_insert_or_delete';
      }
    }
  }
  return null;
}

const stmts = {};
for (const e of batch.events) {
  for (const emb of e.embed || []) stmts[emb.fact_id] = emb.statement;
}

const issues = [];
for (const [fid, para] of Object.entries(P)) {
  if (!(fid in stmts)) continue;
  const stmt = stmts[fid];
  const swc = stmt.replace(/\.$/, '').split(/\s+/).filter(Boolean).length;
  const pwc = para.split(/\s+/).filter(Boolean).length;
  if (Math.abs(pwc - swc) > 2) issues.push(`${fid} wc para=${pwc} stmt=${swc}`);
  const kind = nearVerbatimKind(stmt, para);
  if (kind) issues.push(`${fid} ${kind}: ${para}`);
  if (HEDGE.test(para)) issues.push(`${fid} hedge`);
  if (stmt.replace(/\.$/, '') === para || stmt === para) issues.push(`${fid} verbatim`);
}

const missing = Object.keys(stmts).filter((fid) => !(fid in P));
const lines = ['Checking paraphrases...', `issues ${issues.length}`];
for (const i of issues) lines.push(i);
lines.push(`missing paraphrases ${JSON.stringify(missing)}`);
console.log(lines.join('\n'));
