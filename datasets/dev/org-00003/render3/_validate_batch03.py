import json, re
from pathlib import Path

base = Path("/Users/radiohead/Dev/memory-bench/datasets/dev/org-00003/render3")

try:
    inp = json.loads((base / "batch-03.json").read_text())
except json.JSONDecodeError as e:
    print(f"INVALID INPUT JSON: {e}")
    raise SystemExit(1)
try:
    out = json.loads((base / "batch-03.out.json").read_text())
except json.JSONDecodeError as e:
    print(f"INVALID OUTPUT JSON: {e}")
    raise SystemExit(1)

EMPH = re.compile(r"(!|\*\*|IMPORTANT|REMINDER|NOTE:)")
MARKER = re.compile(r"⟦(F-\d+)⟧(.*?)⟦/\1⟧", re.DOTALL)

def norm(s):
    s = re.sub(r"[^\w\s]", " ", s.lower().strip())
    return re.sub(r"\s+", " ", s)

def classify(stmt, inner):
    na, nb = norm(stmt), norm(inner)
    wa, wb = na.split(), nb.split()
    if na == nb:
        return "exact"
    if len(wa) == len(wb):
        diffs = [i for i, (a, b) in enumerate(zip(wa, wb)) if a != b]
        if len(diffs) == 1:
            return "one_word_swap"
    if abs(len(wa) - len(wb)) == 1:
        longer, shorter = (wa, wb) if len(wa) > len(wb) else (wb, wa)
        for i in range(len(longer)):
            if longer[:i] + longer[i + 1 :] == shorter:
                return "one_word_ins_del"
    return None

issues = []
batch_ids = {e["event_id"] for e in inp["events"]}
out_ids = set(out)
for x in sorted(batch_ids - out_ids):
    issues.append(f"missing {x}")
for x in sorted(out_ids - batch_ids):
    issues.append(f"extra {x}")

lines = []
for ev in inp["events"]:
    eid = ev["event_id"]
    if eid not in out:
        lines.append(f"{eid}: MISSING")
        continue
    text = out[eid]
    cleaned = MARKER.sub(lambda m: m.group(2), text)
    wc = len([w for w in cleaned.split() if w])
    lo, hi = ev["length_words"]
    status = "OK" if lo <= wc <= hi else "FAIL"
    lines.append(f"{eid}: {wc} [{lo},{hi}] {status}")
    if status == "FAIL":
        issues.append(f"{eid}: wc={wc} not in [{lo},{hi}]")
    text_lines = text.split("\n")
    if text_lines[0].find("⟦F-") >= 0:
        issues.append(f"{eid}: embed on first line")
    if text_lines[-1].find("⟦F-") >= 0:
        issues.append(f"{eid}: embed on last line")
    parts = {p["name"] for p in ev["participants"]}
    for line in text.split("\n"):
        if line.startswith("-"):
            continue
        if ":" in line:
            sp = line.split(":", 1)[0]
            if sp not in parts:
                issues.append(f"{eid}: bad speaker {sp!r}")
    found = re.findall(r"⟦(F-\d+)⟧", text)
    expect = [e["fact_id"] for e in ev["embed"]]
    if found != expect:
        issues.append(f"{eid}: markers {found} != {expect}")
    if ev.get("canary"):
        if ev["canary"] not in text:
            issues.append(f"{eid}: missing canary")
        elif text.count(ev["canary"]) != 1:
            issues.append(f"{eid}: canary count={text.count(ev['canary'])}")
    for emb in ev["embed"]:
        fid, stmt, speaker = emb["fact_id"], emb["statement"], emb["speaker"]
        ms = list(re.finditer(re.escape(f"⟦{fid}⟧") + r"(.*?)" + re.escape(f"⟦/{fid}⟧"), text, re.DOTALL))
        if len(ms) != 1:
            issues.append(f"{eid} {fid} count={len(ms)}")
            continue
        inner = ms[0].group(1)
        swc = len(stmt.split())
        iwc = len(inner.split())
        if abs(swc - iwc) > 2:
            issues.append(f"{eid} {fid}: para wc {iwc} vs stmt {swc} (Δ{iwc-swc})")
        kind = classify(stmt, inner)
        if kind:
            issues.append(f"{eid} {fid}: NEAR_VERBATIM [{kind}]\n  stmt: {stmt}\n  inner: {inner}")
        if EMPH.search(inner):
            issues.append(f"{eid} {fid}: emph")
        caps = re.findall(r"\b[A-Z]{4,}\b", inner)
        if caps:
            issues.append(f"{eid} {fid}: CAPS {caps}")
        before = text[: ms[0].start()]
        li = before.count("\n")
        sm = re.match(r"^([^:\n]+):", text.split("\n")[li])
        if not sm or sm.group(1).strip() != speaker:
            issues.append(f"{eid} {fid}: speaker want {speaker} got {sm.group(1) if sm else None}")
        if stmt in text:
            issues.append(f"{eid} {fid}: verbatim present")
        lines.append(f"  {fid}: stmt={swc} para={iwc} Δ={iwc-swc} kind={kind}")

result = "\n".join(lines) + "\n" + ("ISSUES\n" + "\n".join(issues) if issues else "ALL OK")
print(result)
