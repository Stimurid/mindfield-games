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


# ── Second-pass: micro-cards inside top-level entries ───────────────────────
_RE_NUMBERED = re.compile(r"^(\d{1,3})\\?\.\s+(.+)$")
_RE_BULLET   = re.compile(r"^[*\-]\s+(.+)$")
# Label-value lines inside breeds, R-roots etc. — Cyrillic capital then short label, colon, value.
_RE_LABELED  = re.compile(r"^([А-ЯA-Z][а-яёA-Za-zё \-/]{1,30}):\s+(.+?)\s*$")
_RE_TRIPLE_M = re.compile(r"Малое упражнение[:\s]+[“\"«]?(.+?)[”\"»]?\s*[—\-]\s*(.+?)(?=Игра-упражнение|$)")
_RE_TRIPLE_G = re.compile(r"Игра[-‑]упражнение[:\s]+[“\"«]?(.+?)[”\"»]?\s*[—\-]\s*(.+?)(?=Большой симулятор|$)")
_RE_TRIPLE_B = re.compile(r"Большой симулятор[:\s]+[“\"«]?(.+?)[”\"»]?\s*[—\-]\s*(.+?)\s*$")

# Top-level heading detectors share code with parse_corpus but only need to know
# WHICH parent we're under right now.
_TOP_LEVEL_RES = [
    (_RE_ATTRACTOR_V2, lambda m, ctx: f"A{m.group(1)}_{ctx}"),
    (_RE_R_ROOT,       lambda m, ctx: f"R{m.group(1).zfill(2)}"),
    (_RE_BREED,        lambda m, ctx: f"breed_{m.group(1).zfill(2)}"),
    (_RE_PRECARD,      lambda m, ctx: f"precard_{m.group(1).zfill(2)}"),
    (_RE_RESIDUAL,     lambda m, ctx: f"residual_{m.group(1).zfill(2)}"),
    (_RE_GENOME,       lambda m, ctx: f"genome_{m.group(1)}"),
    (_RE_APPSPEC,      lambda m, ctx: f"appspec_{m.group(1)}"),
    (_RE_CHIMERA_V2,   lambda m, ctx: f"chimera_{ctx}_{m.group(1).zfill(3)}"),
]


def parse_micro_cards(path: Path) -> tuple[list[dict], list[tuple[str, str]]]:
    """Returns (entries, parent_links) where parent_links is [(parent_code, child_code)]."""
    if not path.exists():
        return [], []
    lines = _read_lines(path)
    entries: list[dict] = []
    parent_links: list[tuple[str, str]] = []

    current_parent_code: str | None = None
    attractor_ctx = "v0.2"
    chimera_ctx = ""
    in_chim_v01 = in_chim_v02 = False
    counter_in_parent = 0
    seen_codes: set[str] = set()

    def emit(title: str, body: str, kind: str, line_idx: int):
        nonlocal counter_in_parent
        if not current_parent_code:
            return
        counter_in_parent += 1
        code = f"mc_{current_parent_code}_{counter_in_parent:03d}"
        if code in seen_codes:
            return
        seen_codes.add(code)
        entries.append({
            "kind": kind,
            "code": code,
            "title": title[:120].rstrip(),
            "body_md": body,
            "source_pass": "v0.3",
            "source_line": line_idx + 1,
            "order_key": line_idx,
        })
        parent_links.append((current_parent_code, code))

    CAP_PER_PARENT = 40  # avoid runaway accumulation in long unstructured bodies

    for i, raw in enumerate(lines):
        line = raw.rstrip()

        # Track which attractor map / chimera section we're in.
        if line.startswith("## ") and "Семейства-аттракторы v0.1" in line:
            attractor_ctx = "v0.1"
            in_chim_v01 = in_chim_v02 = False
        elif line.startswith("## ") and "Карта аттракторов v0.2" in line:
            attractor_ctx = "v0.2"
            in_chim_v01 = in_chim_v02 = False
        elif line.startswith("## ") and "Химерная матрица v0.1" in line:
            in_chim_v01, in_chim_v02 = True, False
            chimera_ctx = "v0.1"
        elif line.startswith("## ") and "Химерная матрица v0.2" in line:
            in_chim_v01, in_chim_v02 = False, True
            chimera_ctx = "v0.2"

        # Did we enter a new top-level entry? Reset the per-parent counter.
        matched_top = False
        for rx, code_fn in _TOP_LEVEL_RES:
            m = rx.match(line)
            if m:
                if rx is _RE_CHIMERA_V2:
                    if not (in_chim_v01 or in_chim_v02):
                        continue
                    current_parent_code = code_fn(m, chimera_ctx)
                elif rx is _RE_ATTRACTOR_V2:
                    current_parent_code = code_fn(m, attractor_ctx)
                else:
                    current_parent_code = code_fn(m, "")
                counter_in_parent = 0
                matched_top = True
                break
        if matched_top:
            continue

        # Any other top-level / sub-level heading closes the current parent
        # window, so wandering bullets after a section's end stop accumulating.
        if line.startswith("## ") or line.startswith("### "):
            current_parent_code = None
            counter_in_parent = 0
            continue

        if current_parent_code is None or counter_in_parent >= CAP_PER_PARENT:
            continue

        # Numbered list item
        nm = _RE_NUMBERED.match(line)
        if nm:
            body = nm.group(2).strip()
            if len(body) > 6:  # skip noise like "1. x"
                emit(body, body, "micro_numbered", i)
                continue

        # Bullet list item
        bm = _RE_BULLET.match(line)
        if bm:
            body = bm.group(1).strip()
            if len(body) > 6:
                emit(body, body, "micro_bullet", i)
                continue

        # Triple: Малое / Игра / Большой — checked BEFORE the labeled-aspect
        # branch because the triple line is structured as 'Label: value. Label: value.'
        # and would otherwise consume the first segment as an aspect.
        is_triple = ("Малое упражнение" in line or "Игра-упражнение" in line or "Большой симулятор" in line)
        if is_triple:
            for label, rx in (("малое", _RE_TRIPLE_M), ("игра", _RE_TRIPLE_G), ("большой", _RE_TRIPLE_B)):
                m = rx.search(line)
                if m:
                    name = m.group(1).strip().strip("«»\"“”")
                    desc = m.group(2).strip()
                    title = f"{label}: {name}"
                    body = f"{title} — {desc}"
                    emit(title, body, "micro_game", i)
            continue

        # Labeled aspect line (Источник: / Функция: / LLM-роль: ...)
        lab = _RE_LABELED.match(line.strip())
        if lab and not nm and not bm:
            label = lab.group(1).strip()
            value = lab.group(2).strip()
            if (len(label.split()) <= 4 and len(value) >= 8 and len(value) <= 400
                    and not value.endswith(",") and not label.startswith("Это ")):
                title = f"{label}: {value[:60]}"
                emit(title, line.strip(), "micro_aspect", i)
                continue

        # (Triple already handled above; this old branch removed.)
        if False and ("Малое упражнение" in line or "Игра-упражнение" in line or "Большой симулятор" in line):
            for label, rx in (("малое", _RE_TRIPLE_M), ("игра", _RE_TRIPLE_G), ("большой", _RE_TRIPLE_B)):
                m = rx.search(line)
                if m:
                    name = m.group(1).strip().strip("«»\"“”")
                    desc = m.group(2).strip()
                    title = f"{label}: {name}"
                    body = f"{title} — {desc}"
                    emit(title, body, "micro_game", i)

    return entries, parent_links


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
