#!/usr/bin/env python3
"""Manual precheck of paraphrases"""
import json
import re
from pathlib import Path

BATCH_PATH = Path("/Users/radiohead/Dev/memory-bench/datasets/dev/org-00002-twin/render/batch-01.json")

HEDGE = re.compile(
    r"\b(i think|i believe|for what it's worth|maybe|probably|sort of|kind of|arguably)\b",
    re.I,
)
CAPS = re.compile(r"\b[A-Z]{4,}\b")

P = {
    "F-0010": "Company Sev-1 postmortems may forgo the five-whys template when root causes are already known",
    "F-0013": "The company maintained a deploy freeze throughout the Black Friday traffic peak",
    "F-0015": "Growth Sev-2 postmortems might drop timelines when writers stay double-booked",
    "F-0016": "Partner escalations may wait until the following business day for acknowledgment through the shared support alias",
    "F-0021": "Partner escalations might wait forty-five minutes with only junior staff on rotation",
    "F-0031": "Company services may keep shipping features after fully draining the monthly error budget",
    "F-0037": "Quarterly capacity plans may leave out any contingency buffer when headcount stays stable",
    "F-0042": "Quarterly capacity plans might apply a five-percent buffer while hiring remains frozen",
    "F-0051": "Feature flags company-wide may remain temporary indefinitely without a retirement date",
    "F-0054": "The latest infra hire completed a four-interview loop in eight business days",
    "F-0057": "Company runbooks require review only after a related Sev-1 incident occurs",
    "F-0077": "Growth launches may finish checklist sign-off after go-live lacking penalty",
    "F-0096": "Growth Sev-2 postmortems might hold experiment impact numbers when analysts stay offline",
    "F-0097": "Growth permits unlimited unfinished stories to carry into the next sprint",
    "F-0111": "Company feature flags may stay temporary lacking any retirement deadline after creation",
    "F-0114": "Infra cleared eighteen prod access requests amid last week's incident surge",
    "F-0116": "Company feature flags might remain temporary for ninety days if owners are understaffed",
    "F-0117": "Growth may bypass design docs for changes at any estimated engineer-day size",
    "F-0120": "Growth held office hours drawing twenty-two attendees across four sessions last month",
    "F-0043": "Growth can revise quarterly list prices at any time via a Slack note",
    "F-0086": "Schema migrations on infra require a written rollback note before merge",
    "F-0103": "Production releases from infra ship only on the last Friday each month",
    "F-0092": "Growth Sev-2 postmortems can skip experiment impact figures for internal-only incidents",
    "F-0112": "Experiment flags on Growth may stay active for ninety days after experiment end",
    "F-0113": "Marco prefers to keep his personal flags live for thirty days after rollout",
    "F-0073": "Priya prefers to file security review tickets the week after launch",
    "F-0001": "Growth ships production releases only once monthly on the last Friday",
    "F-0022": "Vendor invoices for infra under fifteen thousand dollars may be paid without finance review",
    "F-0047": "Production database migrations on infra may merge with a single self-approval",
    "F-0087": "Webhook path segments for Growth may use singular camelCase nouns",
    "F-0033": "Lena prefers to ship through her full personal error budget before pausing launches",
    "F-0005": "Standups on Growth run for forty-five minutes covering full ticket-by-ticket status",
    "F-0017": "Escalations from partners may wait two business days for acknowledgment via the shared support alias",
    "F-0019": "Slack response targets for Growth are posted under Comms in the team handbook",
    "F-0038": "Capacity plans each quarter may drop contingency buffers during hiring freezes",
    "F-0060": "Brand voice examples company-wide are linked under Voice in the marketing handbook",
    "F-0071": "Customer-data features company-wide may skip security review before production launch",
    "F-0078": "Launches on Growth may finish checklist sign-off the morning of go-live",
    "F-0091": "Sev-1 postmortems company-wide may omit customer segment lists when leadership already knows",
    "F-0098": "Growth allows five unfinished stories to keep rolling into the next sprint",
    "F-0122": "Growth might waive design docs above five engineer-days when architects stay offline",
    "F-0026": "Bug triage on infra is handled ad hoc by whoever files the first comment",
    "F-0011": "Sev-2 postmortems on Growth may omit the customer-impact timeline for internal-only outages",
    "F-0032": "Growth may continue rolling out experiments after fully draining the team error budget",
    "F-0072": "Payment changes on Growth may skip security review until after production launch",
    "F-0012": "Marco prefers drafting postmortems as polished narrative prose before any outline",
    "F-0045": "Priya prefers to pay infra on-call as a flat weekly stipend",
    "F-0052": "Experiment flags on Growth may stay active for six months after experiment end",
    "F-0107": "Support on Growth must get manager approval for every refund above ten dollars",
    "F-0067": "Infra allows unlimited sprint carryover so long as tickets remain assigned",
    "F-0053": "Lena prefers to keep her personal flags live for at least sixty days after rollout",
    "F-0063": "Growth public API paths rely on camelCase resource names",
    "F-0083": "Schema migrations on Growth may merge without any written rollback note",
    "F-0034": "Diego prefers to end Friday pager handoffs with a three-bullet Loom summary",
    "F-0058": "Runbooks company-wide need review only during annual compliance audits",
    "F-0074": "On-call escalation steps for infra are summarized under Escalation in the ops wiki",
    "F-0094": "Anouk prefers to pause her experiments at forty percent team error-budget burn",
    "F-0102": "Growth might allow four unfinished stories to keep rolling when the sprint is understaffed",
    "F-0118": "Growth can omit design docs unless a change exceeds eight engineer-days",
    "F-0093": "Felix prefers to assign postmortem action owners only after the final write-up",
    "F-0018": "Escalations from partners may wait until weekly partner sync for acknowledgment via the shared support alias",
    "F-0036": "Growth might freeze experiments only after fully exhausting the team error budget",
    "F-0039": "Capacity plans each quarter may book teams at one-hundred-percent utilization with no buffer",
    "F-0040": "Wren prefers to keep new services above eighty percent unit test coverage",
    "F-0059": "Runbooks company-wide need no scheduled review once published",
    "F-0079": "Launches on Growth may skip checklist sign-off for dark flag-only ships",
    "F-0080": "Quarterly pricing sheets for Growth are stored under Pricing in the finance drive",
    "F-0099": "Growth allows every unfinished story to keep rolling into the next sprint unchecked",
    "F-0100": "Two vendor contracts were closed by infra after four redline rounds last quarter",
    "F-0119": "Growth may skip design docs for every multi-service change under a flag",
}

batch = json.loads(BATCH_PATH.read_text())
stmts = {
    emb["fact_id"]: emb["statement"]
    for e in batch["events"]
    for emb in e["embed"]
}

pre = []
for fid, stmt in stmts.items():
    if fid not in P:
        pre.append(f"missing {fid}")
        continue
    inner = P[fid]
    swc = len(re.sub(r"\.$", "", stmt).split())
    pwc = len(inner.split())
    if abs(pwc - swc) > 2:
        pre.append(f"{fid} wc para={pwc} stmt={swc} | stmt={stmt!r} | para={inner!r}")
    if HEDGE.search(inner):
        pre.append(f"{fid} hedge | para={inner!r}")
    for cm in CAPS.finditer(inner):
        pre.append(f"{fid} ALLCAPS {cm.group(0)} | para={inner!r}")

if pre:
    print("PRECHECK FAILURES", len(pre))
    for p in pre:
        print(p)
else:
    print("ALL PRECHECKS PASSED")
