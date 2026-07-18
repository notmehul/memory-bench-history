#!/usr/bin/env python3
"""Full clean-room verification over all seeds + twins. Prints a table."""

import json
import sys
from pathlib import Path

from membench.generator import OrgConfig, check_g1, design_org, plan_facts
from membench.generator.realization import _strip_canonicals, check_realization
from membench.generator.stream_linter import lint_stream
from membench.realize import load_annotated

TWIN_COORD_KEYS = ("tier", "scope_ref", "visibility", "author", "capacity",
                   "evidence_events", "distractor")


def main() -> int:
    fails = 0
    for s in range(1, 6):
        d = Path(f"datasets/dev/org-{s:05d}")
        org = json.loads((d / "org.json").read_text())
        pristine = plan_facts(design_org(OrgConfig(seed=s))).org
        struct = json.dumps(_strip_canonicals(org), sort_keys=True) == \
            json.dumps(_strip_canonicals(pristine), sort_keys=True)
        rep = check_realization(pristine, org)
        g1 = check_g1(org, json.loads((d / "plan.json").read_text())["probe_plans"])
        lint = lint_stream(org, load_annotated(d / "events.annotated.jsonl"))
        ok = struct and rep.ok and g1.ok and lint.ok
        fails += 0 if ok else 1
        print(f"seed {s}: struct={'OK' if struct else 'DRIFT'} "
              f"realization={'OK' if rep.ok else 'FAIL'} "
              f"G1={'OK' if g1.ok else 'FAIL'} "
              f"stream={'OK' if lint.ok else 'FAIL'} "
              f"(salience p: {lint.stats.get('p_len')}/{lint.stats.get('p_pos')}"
              f"/{lint.stats.get('p_emph')}, noise {lint.stats.get('noise_floor')})")
        if not g1.ok:
            print("   G1:", g1.failures[:3])
        if not lint.ok:
            print("   lint:", lint.failures[:3])

        td = Path(f"datasets/dev/org-{s:05d}-twin")
        torg = json.loads((td / "org.json").read_text())
        tlint = lint_stream(torg, load_annotated(td / "events.annotated.jsonl"))
        base_by = {f["fact_id"]: f for f in org["facts"]}
        coords = all(
            all(f[k] == base_by[f["fact_id"]][k] for k in TWIN_COORD_KEYS)
            and (("counterfactual" not in f) or
                 (f["canonical"] == base_by[f["fact_id"]]["counterfactual"]["canonical"]))
            for f in torg["facts"]
        )
        tok = tlint.ok and coords
        fails += 0 if tok else 1
        print(f"  twin {s}: stream={'OK' if tlint.ok else 'FAIL'} "
              f"coords={'OK' if coords else 'FAIL'} "
              f"(salience p: {tlint.stats.get('p_len')}/{tlint.stats.get('p_pos')}"
              f"/{tlint.stats.get('p_emph')})")
        if not tlint.ok:
            print("   lint:", tlint.failures[:3])
    print(f"\nSWEEP: {'ALL GREEN' if fails == 0 else f'{fails} FAILURES'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
