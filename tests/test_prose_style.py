"""House style on the surfaces a reader outside the project actually sees.

The `unslop` pass of 2026-09-14 cleared these files; this keeps them cleared.
Scope is deliberately narrow. Dated records (`docs/decision-log.md`,
`docs/validation-report.md`, `CHANGELOG.md`) are deliberately excluded: they are
evidence, and evidence is never restyled after the fact.

If a rule here ever blocks something genuinely right, change the rule in this
file with a reason, rather than working around it in the prose.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

PUBLIC = [
    "README.md",
    "paper/draft.md",
    "paper/checklist.md",
    "docs/vision.md",
    "docs/architecture.md",
    "scripts/release.py",          # its strings ship inside the release bundle
]

# An em dash inside a table cell marks an empty cell, not a sentence connector.
EMPTY_CELL = re.compile(r"\|\s*—\s*\|")

AI_VOCABULARY = (
    "crucial", "delve", "enduring", "fostering", "garner", "interplay",
    "intricate", "pivotal", "showcase", "tapestry", "testament", "underscore",
    "vibrant", "additionally", "leverage", "utilize", "facilitate", "numerous",
    "seamless", "holistic", "groundbreaking", "renowned", "comprehensive",
)

# Abstract metaphor nouns that almost always have a plainer concrete word.
# "harness" is exempt: in this project it is the literal thing (codex-cli), not
# a metaphor.
JARGON = (
    "substrate", "bedrock", "scaffolding", "modality", "paradigm",
    "north star", "flywheel", "endgame", "locus", "nexus", "vantage",
)

FANCY_IS = ("serves as", "stands as", "boasts")

FILLER = ("in order to", "due to the fact that", "it is important to note",
          "it should be noted", "needless to say")


def _text(rel: str) -> str:
    return (ROOT / rel).read_text()


@pytest.mark.parametrize("rel", PUBLIC)
def test_no_em_dashes(rel: str):
    lines = [(i, line) for i, line in enumerate(_text(rel).splitlines(), 1)
             if "—" in line and not EMPTY_CELL.search(line)]
    assert not lines, (
        f"{rel}: em dashes on lines {[i for i, _ in lines]}. End the sentence or "
        "use a comma; do not swap in parentheses or an en dash.")


@pytest.mark.parametrize("rel", PUBLIC)
def test_no_curly_quotes(rel: str):
    assert not any(c in _text(rel) for c in "“”‘’"), f"{rel}: use straight quotes"


@pytest.mark.parametrize("rel", PUBLIC)
def test_no_ai_vocabulary(rel: str):
    t = _text(rel)
    hits = [w for w in AI_VOCABULARY if re.search(rf"\b{re.escape(w)}\b", t, re.I)]
    assert not hits, f"{rel}: {hits} — use the plain word"


@pytest.mark.parametrize("rel", PUBLIC)
def test_no_abstract_metaphor_nouns(rel: str):
    t = _text(rel)
    hits = [w for w in JARGON if re.search(rf"\b{re.escape(w)}\b", t, re.I)]
    assert not hits, f"{rel}: {hits} — name the concrete thing"


@pytest.mark.parametrize("rel", PUBLIC)
def test_no_padding(rel: str):
    t = _text(rel)
    hits = [w for w in FANCY_IS + FILLER if re.search(rf"\b{re.escape(w)}\b", t, re.I)]
    assert not hits, f"{rel}: {hits} — say 'is'/'has', or cut the filler"
