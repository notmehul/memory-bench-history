"""Export the public repository from this private one.

An allowlist, not a denylist: a file reaches the public tree only if a rule
below names it. Only git-tracked files are considered, so nothing untracked in
this working copy can ride along. Withheld names, holdout seeds and generator
source are removed again after the allowlist, as a second guard, and the result
must pass scripts/leak_audit.py before it is used.

    python scripts/export_public.py ../memory-bench-public

What stays private, and why, is scripts/release.py's policy: the ledger, probe
plans, realization maps, annotated streams, the generator (a deterministic
function of the seed that rebuilds holdout ledgers), holdout seeds 4-5 and every
rater key. Construction tooling and the dated working record (decision log,
status, plan) live in the history repository instead.
"""

from __future__ import annotations

import argparse
import fnmatch
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from leak_audit import GENERATOR_PATHS, HOLDOUT_DIRS  # noqa: E402
from release import WITHHELD_NAMES  # noqa: E402

PUBLIC_SCRIPTS = ("calibration", "calibration_sheet", "exploit_audit", "figures",
                  "g3_summary", "leak_audit", "methods_judge_panel",
                  "methods_verdict_kinds", "power_analysis", "release", "run_pilot",
                  "score_sut", "screen_probes")

INCLUDE = (
    "LICENSE", "pyproject.toml", ".github/workflows/*",
    "src/membench/*",
    "prompts/typed-memory-extract.md",   # read at runtime by the typed-memory adapter
    *(f"scripts/{s}.py" for s in PUBLIC_SCRIPTS),
    "tests/*",
    "docs/vision.md", "docs/architecture.md", "docs/power-analysis.md",
    "docs/human-review.md", "docs/vendor-configs.md", "docs/vendor-survey.md",
    "docs/validation-report.md",
    "docs/specs/*",
    "paper/memory-bench.tex", "paper/pipeline.tex",
    "datasets/dev/org-0000[123]/g3-report.json",
    "datasets/dev/org-0000[123]/consistency-report.json",
    "datasets/dev/org-0000[123]/g1-report.txt",
    "datasets/dev/screening/org-0000[123]/*",
    "datasets/dev/screening/exploit-audit/*",
    "datasets/dev/screening/judge-decoys/*",
    "datasets/dev/screening/harness-study-2026-07-25/*",
    "datasets/dev/screening/sub07-sensitivity/*",
    "datasets/dev/calibration/*",
    "datasets/dev/pilot/*",
    "datasets/methods/*",
)

EXCLUDE = (
    "tests/test_generator.py", "tests/test_renderer.py", "tests/test_twin.py",
)

# Files that exist only in the public tree: written here, copied over the export.
OVERLAY = ROOT / "public"
BUILT = ("paper/srivastava-2026-memory-bench.pdf",
         "paper/srivastava-2026-constructing-a-benchmark.pdf")


def selected(path: str) -> bool:
    parts = path.split("/")
    if not any(fnmatch.fnmatch(path, g) for g in INCLUDE):
        return False
    if path in EXCLUDE or parts[-1] in WITHHELD_NAMES:
        return False
    if any(p.startswith(HOLDOUT_DIRS) for p in parts):
        return False
    return not any(path == g or path.startswith(g) for g in GENERATOR_PATHS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    args = ap.parse_args(argv)
    out: Path = args.out.resolve()
    if out.exists() and any(p.name != ".git" for p in out.iterdir()):
        for p in out.iterdir():
            if p.name != ".git":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    out.mkdir(parents=True, exist_ok=True)

    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True,
                             text=True, check=True).stdout.splitlines()
    chosen = [p for p in tracked if selected(p)]
    for rel in [*chosen, *BUILT]:
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    overlay = [p for p in OVERLAY.rglob("*") if p.is_file()]
    for src in overlay:
        dst = out / src.relative_to(OVERLAY)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"exported {len(chosen)} tracked files, {len(BUILT)} built papers and "
          f"{len(overlay)} overlay files to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
