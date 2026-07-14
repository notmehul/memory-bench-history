#!/usr/bin/env python3
"""Faithful port of datasets/dev/org-00004-twin/render/_validate.mjs"""
import json, re, sys

batch = json.load(open("datasets/dev/org-00004-twin/render/batch-01.json"))
out = json.load(open("datasets/dev/org-00004-twin/render/batch-01.out.json"))
EMPH = re.compile(r"(!|\*\*|IMPORTANT|REMINDER|NOTE:)")
issues = []
batch_ids = set(e["event_id"] for e in batch["events"])
out_ids = set(out.keys())
missing = [i for i in batch_ids if i not in out_ids]
extra = [i for i in out_ids if i not in batch_ids]
if missing:
    issues.append(f"missing {missing}")
if extra:
    issues.append(f"extra {extra}")
for t in batch["events"]:
    eid = t["event_id"]
    text = out[eid]
    cleaned = re.sub(r"⟦F-\d{4}⟧([\s\S]*?)⟦/F-\d{4}⟧", r"\1", text)
    wc = len([w for w in cleaned.split() if w])
    lo, hi = t["length_words"]
    if wc < lo or wc > hi:
        issues.append(f"{eid}: wc={wc} not in [{lo},{hi}]")
    found = list(re.finditer(r"⟦(F-\d{4})⟧([\s\S]*?)⟦/\1⟧", text))
    found_ids = [m.group(1) for m in found]
    expect = [e["fact_id"] for e in t["embed"]]
    if found_ids != expect:
        issues.append(f"{eid}: markers {found_ids}!={expect}")
    parts = set(p["name"] for p in t["participants"])
    for line in text.split("\n"):
        if ":" in line:
            sp = line.split(":")[0]
            if sp not in parts:
                issues.append(f'{eid}: speaker {json.dumps(sp)} not in participants')
    if "⟦F-" in text.split("\n")[0]:
        issues.append(f"{eid}: embed first line")
    lines = text.split("\n")
    if "⟦F-" in lines[-1]:
        issues.append(f"{eid}: embed last line")
    for m in found:
        if EMPH.search(m.group(2)):
            issues.append(f"{eid}: emph in {m.group(1)}")
        caps = re.findall(r"\b[A-Z]{4,}\b", m.group(2))
        if caps:
            issues.append(f"{eid}: CAPS {caps} in {m.group(1)}")
        pos = m.start()
        ls = text.rfind("\n", 0, pos) + 1
        le = text.find("\n", pos)
        if le < 0:
            le = len(text)
        sp = text[ls:le].split(":")[0]
        emb = next(e for e in t["embed"] if e["fact_id"] == m.group(1))
        if sp != emb["speaker"]:
            issues.append(f"{eid}: {m.group(1)} by {sp} want {emb['speaker']}")
        if emb["statement"] in text:
            issues.append(f"{eid}: verbatim {m.group(1)}")
        sw = len([w for w in emb["statement"].rstrip(".").split() if w])
        pw = len([w for w in m.group(2).strip().split() if w])
        if abs(pw - sw) > 2:
            issues.append(f"{eid}: {m.group(1)} paraphrase wc={pw} stmt={sw} (Δ{pw-sw})")
    print(f"{eid}: {wc} words [{lo}-{hi}] embeds={json.dumps(found_ids)}")
print("ISSUES:" if issues else "ALL OK")
for i in issues:
    print(f"  {i}")
