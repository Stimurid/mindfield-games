"""Structural parser for docs/spec.md (the original 'игры игры 26.md' / 5190 lines).

We do NOT use an LLM here — the source has stable heading patterns and ingesting
it deterministically means the library is reproducible. Top-level pass only.
Small inline cards (the '4200 games that are not games') are out of scope for
this pass and tracked separately.
"""
from __future__ import annotations
import re
from pathlib import Path

# ── Heading patterns (Markdown bolded headings with Russian content) ──────────
_RE_ATTRACTOR_V2 = re.compile(r"^### \*\*A(\d{2})\\?\. (.+?)\*\*\s*$")
_RE_R_ROOT       = re.compile(r"^### \*\*R(\d{1,2})\\?\. (.+?)\*\*\s*$")
_RE_BREED        = re.compile(r"^## \*\*(\d{1,2})\\?\. Порода [“«\"](.+?)[”»\"]\*\*\s*$")
_RE_PRECARD      = re.compile(r"^### \*\*Карточка (\d+)\\?\. (.+?)\*\*\s*$")
_RE_RESIDUAL     = re.compile(r"^## \*\*Остаток (\d+)\\?\. (.+?)\*\*\s*$")
_RE_CHIMERA_V2   = re.compile(r"^### \*\*(\d{1,3})\\?\. (.+? [×x] .+?)\*\*\s*$")  # broad
_RE_GENOME       = re.compile(r"^## \*\*GENOME (A\d{2})\\?\. (.+?)\*\*\s*$")
_RE_APPSPEC      = re.compile(r"^## \*\*APP (A\d{2})\\?\. (.+?)\*\*\s*$")

# Section gates — body capture stops at the next sibling/parent heading.
_ANY_HEADING = re.compile(r"^#{1,3} ")


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _slice_body(lines: list[str], start_idx: int) -> str:
    """Capture body until the next heading at same/higher level."""
    body: list[str] = []
    for j in range(start_idx + 1, len(lines)):
        if _ANY_HEADING.match(lines[j]):
            break
        body.append(lines[j])
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return "\n".join(body)


def parse_corpus(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = _read_lines(path)
    out: list[dict] = []
    seen_codes: set[str] = set()

    def push(kind: str, code: str, title: str, line_idx: int, source_pass: str, order_key: int):
        if code in seen_codes:
            return
        body = _slice_body(lines, line_idx)
        out.append({
            "kind": kind,
            "code": code,
            "title": title.strip(),
            "body_md": body,
            "source_pass": source_pass,
            "source_line": line_idx + 1,
            "order_key": order_key,
        })
        seen_codes.add(code)

    # Two attractor maps exist. v0.2 is canonical; v0.1 is preserved as 'v0.1'.
    in_v01 = False
    in_v02 = False
    in_chim_v01 = False
    in_chim_v02 = False
    for i, line in enumerate(lines):
        if line.startswith("## ") and "Семейства-аттракторы v0.1" in line:
            in_v01 = True
            in_v02 = False
        elif line.startswith("## ") and "Карта аттракторов v0.2" in line:
            in_v01 = False
            in_v02 = True
        elif line.startswith("## ") and "Химерная матрица v0.1" in line:
            in_chim_v01 = True
            in_chim_v02 = False
            in_v01 = in_v02 = False
        elif line.startswith("## ") and "Химерная матрица v0.2" in line:
            in_chim_v01 = False
            in_chim_v02 = True
        elif line.startswith("## ") and ("Сжатие матрицы" in line or "Что матрица" in line):
            in_chim_v01 = in_chim_v02 = False
        elif line.startswith("## "):
            # any other "## " heading closes attractor windows
            in_v01 = False
            in_v02 = False

        m = _RE_ATTRACTOR_V2.match(line)
        if m:
            num, title = m.group(1), m.group(2)
            tag = "v0.1" if in_v01 else "v0.2"
            code = f"A{num}_{tag}"
            push("attractor", code, title, i, tag, int(num))
            continue

        m = _RE_R_ROOT.match(line)
        if m:
            num, title = m.group(1).zfill(2), m.group(2)
            push("r_root", f"R{num}", title, i, "v0.3", int(num))
            continue

        m = _RE_BREED.match(line)
        if m:
            num, title = m.group(1).zfill(2), m.group(2)
            push("breed", f"breed_{num}", title, i, "v0.3", int(num))
            continue

        m = _RE_PRECARD.match(line)
        if m:
            num, title = m.group(1).zfill(2), m.group(2)
            push("precard", f"precard_{num}", title, i, "v0.0", int(num))
            continue

        m = _RE_RESIDUAL.match(line)
        if m:
            num, title = m.group(1).zfill(2), m.group(2)
            push("residual", f"residual_{num}", title, i, "v0.3", int(num))
            continue

        m = _RE_GENOME.match(line)
        if m:
            ax, title = m.group(1), m.group(2)
            push("genome", f"genome_{ax}", title, i, "v0.3", int(ax[1:]))
            continue

        m = _RE_APPSPEC.match(line)
        if m:
            ax, title = m.group(1), m.group(2)
            push("appspec", f"appspec_{ax}", title, i, "v0.3", int(ax[1:]))
            continue

        if in_chim_v01 or in_chim_v02:
            m = _RE_CHIMERA_V2.match(line)
            if m:
                num, title = m.group(1).zfill(3), m.group(2)
                tag = "v0.1" if in_chim_v01 else "v0.2"
                push("chimera", f"chimera_{tag}_{num}", title, i, tag, int(num))

    return out


def parse_phase_docs(docs_dir: Path) -> list[dict]:
    """Ingest our own design / playtest / acceptance docs as corpus entries."""
    out: list[dict] = []
    if not docs_dir.exists():
        return out
    for i, fp in enumerate(sorted(docs_dir.glob("*.md"))):
        if fp.name == "spec.md":
            continue  # source, parsed structurally above
        title = fp.stem.replace("_", " ").replace("-", " ").title()
        out.append({
            "kind": "phase_doc",
            "code": f"doc_{fp.stem}",
            "title": title,
            "body_md": fp.read_text(encoding="utf-8"),
            "source_pass": "phase",
            "source_line": None,
            "order_key": i,
        })
    return out
