"""Check a tree, or every blob in a git history, for material the release withholds.

`release.py verify` checks a built bundle. This checks anything else that is
about to become public: a source tree, or a repository's full history, where a
file deleted in the latest commit is still one `git show` away.

Needs the private ledger (`--private datasets/dev`) as its reference, so it runs
where the answers live and nowhere else.

    python scripts/leak_audit.py --private datasets/dev tree ../memory-bench-public
    python scripts/leak_audit.py --private datasets/dev history ../history.git

Fails on:
  - a withheld filename (release.WITHHELD_NAMES), anywhere in the target
  - a holdout seed's directory (org-00004, org-00005 and their twins)
  - a fact ledger under any file name (JSON whose `facts` are fact records)
  - generator source (release.py withholds it: it rebuilds holdout ledgers)
  - any HOLDOUT fact's canonical or counterfactual text, verbatim, anywhere.

Reported but allowed: public-seed ledger text. The shipped streams carry some
facts in canonical wording (seed 2's twin carries 24 of 123), and screening
evidence carries probed facts by construction, since the ceiling condition
injects them. What a public seed withholds is the ledger as an object, which
labels facts probed or distractor; the path and org.json rules cover that.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release import HOLDOUT_SEEDS, WITHHELD_NAMES  # noqa: E402

GENERATOR_PATHS = ("src/membench/generator/", "src/membench/generate.py",
                   "src/membench/pipeline.py", "src/membench/realize.py")
HOLDOUT_DIRS = tuple(f"org-{s:05d}" for s in HOLDOUT_SEEDS)
MIN_LEN = 24  # shorter canonicals are generic phrases that recur by coincidence


def ledger_strings(private: Path) -> dict[str, str]:
    """Every canonical and counterfactual string, mapped to the org it came from."""
    out: dict[str, str] = {}
    for org_json in sorted(private.glob("org-*/org.json")):
        for fact in json.loads(org_json.read_text()).get("facts", []):
            for key in ("canonical", "counterfactual"):
                text = fact.get(key)
                if isinstance(text, str) and len(text) >= MIN_LEN and not text.startswith("<<"):
                    out.setdefault(text, org_json.parent.name)
    return out


def path_problems(path: str) -> list[str]:
    parts = path.split("/")
    found = []
    if parts[-1] in WITHHELD_NAMES:
        found.append("withheld filename")
    if any(p.startswith(HOLDOUT_DIRS) for p in parts):
        found.append("holdout seed directory")
    if any(path == g or path.startswith(g) for g in GENERATOR_PATHS):
        found.append("generator source")
    return found


def is_ledger(text: str) -> bool:
    """A fact ledger under any file name: JSON whose `facts` are fact records.

    Hand-built test fixtures (`org_id` "fix-...") are exempt by name: they are
    a few synthetic facts for the belief-oracle tests, not a seed's ledger.
    """
    try:
        doc = json.loads(text)
        facts = doc.get("facts")
    except (json.JSONDecodeError, AttributeError):
        return False
    if str(doc.get("org_id", "")).startswith("fix-"):
        return False
    return bool(facts) and isinstance(facts, list) and isinstance(facts[0], dict) \
        and {"fact_id", "canonical"} <= facts[0].keys()


def content_problems(path: str, text: str, ledger: dict[str, str]) -> list[str]:
    found = []
    if path.endswith(".json") and is_ledger(text):
        found.append("a fact ledger (JSON carrying fact records)")
    hits = {org for s, org in ledger.items() if s in text}
    held = sorted(h for h in hits if h.startswith(HOLDOUT_DIRS))
    if held:
        found.append(f"holdout ledger text from {held}")
    return found


def public_text_files(root: Path, ledger: dict[str, str]) -> int:
    public = {s for s, org in ledger.items() if not org.startswith(HOLDOUT_DIRS)}
    return sum(1 for p in root.rglob("*") if p.is_file() and ".git" not in p.parts
               and any(s in p.read_text(errors="ignore") for s in public))


def audit_tree(root: Path, ledger: dict[str, str]) -> list[str]:
    report = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or ".git" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        text = p.read_text(errors="ignore")
        problems = path_problems(rel) + content_problems(rel, text, ledger)
        report += [f"{rel}: {x}" for x in problems]
    return report


def audit_history(repo: Path, ledger: dict[str, str]) -> list[str]:
    """Every blob reachable from any ref, under every path it was committed at."""
    listing = subprocess.run(["git", "-C", str(repo), "rev-list", "--all", "--objects"],
                             capture_output=True, text=True, check=True).stdout
    report, seen = [], set()
    for line in listing.splitlines():
        sha, _, path = line.partition(" ")
        if not path:
            continue
        if (sha, path) in seen:
            continue
        seen.add((sha, path))
        kind = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", sha],
                              capture_output=True, text=True).stdout.strip()
        if kind != "blob":
            continue
        problems = path_problems(path)
        blob = subprocess.run(["git", "-C", str(repo), "cat-file", "-p", sha],
                              capture_output=True).stdout.decode(errors="ignore")
        problems += content_problems(path, blob, ledger)
        report += [f"{path} @ {sha[:10]}: {x}" for x in problems]
    msgs = subprocess.run(["git", "-C", str(repo), "log", "--all", "--format=%H%x00%B%x01"],
                          capture_output=True, text=True, check=True).stdout
    for entry in msgs.split("\x01"):
        sha, _, body = entry.strip().partition("\x00")
        held = sorted({org for s, org in ledger.items() if s in body
                       and org.startswith(HOLDOUT_DIRS)})
        if held:
            report.append(f"commit message {sha[:10]}: holdout ledger text from {held}")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--private", type=Path, required=True,
                    help="directory holding the private org-*/org.json ledgers")
    ap.add_argument("mode", choices=("tree", "history"))
    ap.add_argument("target", type=Path)
    args = ap.parse_args(argv)

    ledger = ledger_strings(args.private)
    if not ledger:
        print("no ledger strings found under --private; refusing to report a clean audit")
        return 2
    report = (audit_tree if args.mode == "tree" else audit_history)(args.target, ledger)
    for line in report:
        print(f"LEAK {line}")
    orgs = sorted(set(ledger.values()))
    if args.mode == "tree":
        print(f"INFO {public_text_files(args.target, ledger)} files carry public-seed "
              f"ledger text (allowed: shipped streams and screening evidence)")
    print(f"\n{'CLEAN' if not report else f'{len(report)} problem(s)'}: {args.mode} "
          f"{args.target}, checked against {len(ledger)} ledger strings from {len(orgs)} orgs")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
