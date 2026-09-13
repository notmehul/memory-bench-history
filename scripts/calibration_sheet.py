"""G4 rater sheet: the blinded 150-pair calibration packet as an .xlsx, and
the filled sheet back as a ratings JSON for `calibration.py judge-agreement`.

The packet is already blinded — a rater sees a criterion and a deliverable and
nothing else: no run id, no condition (floor/ceiling/twin), no base-vs-
counterfactual side, no probe or cluster id. This script preserves that. The
opaque pair id travels in a column only so the filled sheet can be mapped back;
it carries no information a rater could use.

`export` writes one row per pair with a TRUE/FALSE dropdown, wrapped text, and
the header and answer columns frozen so the answer box stays on screen while a
long deliverable scrolls. `import` validates the sheet the way
`calibration.py` validates a ratings file — every packet id present, exactly
one boolean each, nothing added or renamed — and refuses the file rather than
guessing at a blank or a typo.

Usage:
  python scripts/calibration_sheet.py export <packet_dir> <out.xlsx>
  python scripts/calibration_sheet.py import <in.xlsx> [--packet-dir D] [--out ratings.json]

Needs the `sheet` extra: uv sync --extra sheet
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

HEADERS = ("#", "ANSWER", "CRITERION — does the output satisfy this?",
           "OUTPUT — the deliverable, judge only what is on the page", "id (do not edit)")

OUTPUT_WIDTH = 100          # characters; drives the wrapped-line estimate
MAX_ROW_POINTS = 409        # Excel's hard row-height ceiling
LINE_POINTS = 13.5

TRUTHY = {"true": True, "yes": True, "y": True, "1": True, "t": True}
FALSY = {"false": False, "no": False, "n": False, "0": False, "f": False}

RULES = [
    ("The question", "For each row: does the OUTPUT satisfy the CRITERION? "
                     "Put TRUE or FALSE in the ANSWER column."),
    ("Doubt = FALSE", "TRUE only if the output CLEARLY satisfies the criterion. "
                      "If you are unsure, answer FALSE. This is the protocol, not "
                      "pessimism — the AI judge is held to the same rule."),
    ("Absence criteria", "For criteria phrased as absence ('does not mention X', "
                         "'does not present X as current'): TRUE only if X is "
                         "genuinely not presented as current or applicable. "
                         "Paraphrases and synonyms of X count as present. If X "
                         "appears only as past, replaced, hypothetical, or rejected "
                         "('we no longer do X'), that is NOT presenting it → TRUE."),
    ("Positive criteria", "For criteria demanding content ('states X', 'sets X as "
                          "the rule'): TRUE only if the output actually commits to X. "
                          "If it presents X and a conflicting alternative as both "
                          "current — hedging, listing both — it has not committed → "
                          "FALSE."),
    ("Only what is on the page", "No outside knowledge, no guessing what the writer "
                                 "meant, no partial credit. Quality is not the "
                                 "question; the criterion is. A well-written output "
                                 "that does not address the criterion is FALSE."),
    ("Work forward", "First answers are final. Do not go back to make earlier rows "
                     "consistent with later ones — that drift is part of what this "
                     "measures. Take breaks between blocks; expect 3–5 hours."),
    ("No tools", "No AI assistants, no web searches, no asking anyone. Your unaided "
                 "judgment is the instrument being measured."),
    ("Do not reorder", "Never sort, insert, or delete rows, and do not edit the "
                       "CRITERION, OUTPUT, or id columns. Only the ANSWER column "
                       "changes. Sorting breaks the mapping back to the packet."),
    ("Long outputs", "A few deliverables are longer than one row can show. Click the "
                     "cell and read it in the formula bar (drag its bottom edge to "
                     "make it taller), or widen the row."),
]


def _load_packet(packet_dir: Path) -> list[dict]:
    p = packet_dir / "rater-packet.json"
    if not p.is_file():
        raise SystemExit(f"no rater-packet.json under {packet_dir}")
    return json.loads(p.read_text())


def _row_points(text: str) -> float:
    """Estimate a wrapped row height; Excel cannot auto-fit a wrapped cell."""
    lines = sum(max(1, math.ceil(len(para) / (OUTPUT_WIDTH - 5)))
                for para in text.split("\n"))
    return min(MAX_ROW_POINTS, max(30.0, lines * LINE_POINTS))


# --------------------------------------------------------------------- export

def cmd_export(args) -> int:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    packet = _load_packet(args.packet_dir)
    wb = Workbook()

    # ---- sheet 1: the rules
    how = wb.active
    how.title = "How to rate"
    how.column_dimensions["A"].width = 26
    how.column_dimensions["B"].width = 96
    how["A1"] = "Grader calibration — how to rate"
    how["A1"].font = Font(bold=True, size=14)
    how["A2"] = (f"{len(packet)} rows on the 'Rate' sheet. Fill the ANSWER column, "
                 "save as .xlsx, send it back.")
    how["A2"].alignment = Alignment(wrap_text=True)
    how.merge_cells("A2:B2")
    for i, (head, body) in enumerate(RULES, start=4):
        how.cell(i, 1, head).font = Font(bold=True)
        how.cell(i, 1).alignment = Alignment(vertical="top")
        c = how.cell(i, 2, body)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        how.row_dimensions[i].height = min(MAX_ROW_POINTS, max(30, len(body) / 90 * 15 + 15))

    # ---- sheet 2: the work
    ws = wb.create_sheet("Rate")
    header_fill = PatternFill("solid", fgColor="1F3864")
    for col, name in enumerate(HEADERS, start=1):
        c = ws.cell(1, col, name)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = header_fill
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 34

    for width, col in zip((5, 11, 52, OUTPUT_WIDTH, 16), "ABCDE", strict=True):
        ws.column_dimensions[col].width = width

    top_wrap = Alignment(wrap_text=True, vertical="top")
    for i, row in enumerate(packet, start=2):
        ws.cell(i, 1, i - 1).alignment = Alignment(vertical="top", horizontal="center")
        ws.cell(i, 2).alignment = Alignment(vertical="center", horizontal="center")
        ws.cell(i, 2).font = Font(bold=True, size=12)
        ws.cell(i, 3, row["criterion"]).alignment = top_wrap
        ws.cell(i, 4, row["output"]).alignment = top_wrap
        idc = ws.cell(i, 5, row["id"])
        idc.alignment = Alignment(vertical="top")
        idc.font = Font(color="999999", size=9)
        ws.row_dimensions[i].height = _row_points(row["output"])

    last = len(packet) + 1
    span = f"B2:B{last}"
    dv = DataValidation(type="list", formula1='"TRUE,FALSE"', allow_blank=True,
                        showDropDown=False, errorTitle="TRUE or FALSE",
                        error="Answer TRUE or FALSE. If you are unsure, the protocol "
                              "says FALSE.")
    ws.add_data_validation(dv)
    dv.add(span)
    # unanswered rows glow amber so nothing is missed on a 150-row pass
    ws.conditional_formatting.add(span, FormulaRule(
        formula=["ISBLANK(B2)"], fill=PatternFill("solid", fgColor="FFE699")))

    ws.freeze_panes = "C2"           # header + # and ANSWER stay on screen
    ws.auto_filter.ref = f"A1:E{last}"

    # a live progress counter, so the rater can see what is left
    prog = ws.cell(1, 7, f'=COUNTA(B2:B{last})&" / {len(packet)} answered"')
    prog.font = Font(bold=True)
    ws.column_dimensions[get_column_letter(7)].width = 24

    args.out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.out)
    print(f"{len(packet)} pairs -> {args.out}  (fill column B with TRUE/FALSE)")
    return 0


# --------------------------------------------------------------------- import

def _coerce(value, rownum: int) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or str(value).strip() == "":
        raise SystemExit(f"row {rownum}: no answer — every row needs TRUE or FALSE")
    key = str(value).strip().lower()
    if key in TRUTHY:
        return True
    if key in FALSY:
        return False
    raise SystemExit(f"row {rownum}: {value!r} is not TRUE or FALSE")


def cmd_import(args) -> int:
    from openpyxl import load_workbook

    packet = _load_packet(args.packet_dir)
    want = [r["id"] for r in packet]
    wb = load_workbook(args.xlsx, data_only=True)
    if "Rate" not in wb.sheetnames:
        raise SystemExit(f"{args.xlsx} has no 'Rate' sheet (found {wb.sheetnames})")
    ws = wb["Rate"]

    ratings: dict[str, bool] = {}
    for rownum, row in enumerate(ws.iter_rows(min_row=2, max_col=5, values_only=True),
                                 start=2):
        _, answer, _, _, pair_id = row
        if pair_id is None and answer is None:
            continue
        pair_id = str(pair_id).strip()
        if pair_id in ratings:
            raise SystemExit(f"row {rownum}: duplicate id {pair_id}")
        ratings[pair_id] = _coerce(answer, rownum)

    missing = [i for i in want if i not in ratings]
    extra = sorted(set(ratings) - set(want))
    if missing or extra:
        raise SystemExit(
            f"sheet does not match the packet — {len(missing)} missing "
            f"{missing[:5]}, {len(extra)} unknown {extra[:5]}. Rows were probably "
            "sorted, inserted, or deleted; re-export and re-enter rather than "
            "patching this file.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({i: ratings[i] for i in want}, indent=1))
    n_true = sum(ratings.values())
    print(f"{len(ratings)} ratings -> {args.out}  "
          f"({n_true} TRUE, {len(ratings) - n_true} FALSE)\n"
          f"next: .venv/bin/python scripts/calibration.py judge-agreement "
          f"{args.packet_dir} {args.out} "
          f"datasets/dev/screening/org-00001 datasets/dev/screening/org-00002")
    return 0


# ------------------------------------------------------------------------ cli

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("packet_dir", type=Path)
    e.add_argument("out", type=Path)
    i = sub.add_parser("import")
    i.add_argument("xlsx", type=Path)
    i.add_argument("--packet-dir", type=Path, default=Path("datasets/dev/calibration"))
    i.add_argument("--out", type=Path, default=Path("datasets/dev/calibration/ratings-M.json"))
    args = ap.parse_args(argv)
    return {"export": cmd_export, "import": cmd_import}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
