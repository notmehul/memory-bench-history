#!/bin/sh
set -e
cd /Users/radiohead/Dev/memory-bench
# Restore templated org.json then realize canonicals.
python3 -m membench.generate --seed 1 --out datasets/dev
python3 datasets/dev/org-00001/_realize.py
# Cleanup helpers
rm -f datasets/dev/org-00001/_extract_facts.py \
      datasets/dev/org-00001/_copy.sh \
      datasets/dev/org-00001/_copy_only.py \
      datasets/dev/org-00001/test.txt \
      datasets/dev/org-00001/_run_realize.sh
# Keep _realize.py only if realize succeeded; delete after
python3 - <<'PY'
import json
from pathlib import Path
p = Path("datasets/dev/org-00001/org.realized.json")
o = Path("datasets/dev/org-00001/org.json")
rd = json.loads(p.read_text())
og = json.loads(o.read_text())
assert "<<" not in p.read_text()
c = []
for f in rd["facts"]:
    c.append(f["canonical"])
    if f.get("counterfactual"):
        c.append(f["counterfactual"]["canonical"])
assert len(c) == len(set(c)), f"dupes: {[x for x in c if c.count(x)>1][:5]}"
# non-canonical equality
def strip(d):
    out=[]
    for f in d["facts"]:
        g={k:v for k,v in f.items() if k!="canonical"}
        if "counterfactual" in g and g["counterfactual"]:
            g=dict(g)
            g["counterfactual"]={k:v for k,v in g["counterfactual"].items() if k!="canonical"}
        out.append(g)
    return out
assert strip(rd)==strip(og)
print("OK", len(rd["facts"]), "facts", len(c), "canonicals")
PY
rm -f datasets/dev/org-00001/_realize.py
