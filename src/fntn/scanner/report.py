"""The run report: what the funnel did, rendered from the ledger and nothing else.

**Why a document and not a print.** A scan prints a summary and the summary
scrolls away. What §9.2 asks for is a record a reader can come back to and
compare against another run, and what CLAUDE.md's statement of the product asks
for is a ledger in which every unit of capital withheld was withheld for a
stated reason. Neither survives in terminal scrollback.

**This measures nothing.** Every figure here is read out of the ledger, the
registration and the code registry. The report cannot make a run come out
differently and cannot make one look better: it renders records that already
exist, and where a record does not exist it says so under *not measured* rather
than leaving the section out. It is procedure by §0.6's test, adding no gate, no
family, no grammar row, no cost tier, no feed, no sizing input and no field the
funnel reads at decision time.

**The binding path comes first, above the provenance header.** The provenance
header answers *under what was this run taken*; the binding path answers *has
the project moved*, and a reader opening the file for the second question
should not have to find it under the first. Its five steps are the register's,
in the register's order, and every status is read out of ``docs/OPEN_ITEMS.md``
rather than stated here. **The one judgement in that section is which register
cells settle which step**, and it is printed beside each step so a reader who
disagrees with it can see it rather than infer it.

**The queue's ordering is the second design decision in here, and it is a
refusal.** Drafts are ordered by **how many operator inputs each is still
missing, ascending**, and by nothing else. Any other ordering is a judgement
about which idea deserves attention first, and a judgement made by this file is
a judgement made by the model about which of the operator's decisions matters,
which is the clerk becoming an analyst. Ties break on the directive identifier,
which ranks nothing. There is no merit column, no severity, no score and no
recency, and ``test_the_queue_is_ordered_by_outstanding_count_and_nothing_else``
constructs drafts whose every other ordering disagrees with the count and
asserts the output follows the count.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from . import codes
from .ledger import Ledger
from .params import Registration

#: The four inputs only the operator may supply (§3.6.8 step 4, CLAUDE.md's
#: second hard prohibition).  Named here in one place so the queue reports the
#: same four every run, and so a draft missing one it is not currently refused
#: for is still shown as missing it.
OPERATOR_INPUTS: Tuple[Tuple[str, str], ...] = (
    ("delta_min", "delta_min_absent"),
    ("registered_sign", ""),
    ("pre_mortem", "premortem_unratified"),
    ("literature_search", "literature_search_absent"),
)

#: The three rules this project's own instruments have falsified.  Seeded here
#: rather than in a document nobody updates, because a report with a
#: *refutations* section and nothing in it teaches the reader that the section
#: is decorative.  A run that falsifies a rule adds to this.
STANDING_REFUTATIONS: Tuple[Tuple[str, str, str], ...] = (
    (
        "2026-08-26",
        "The entity fence can be a pattern over an open vocabulary",
        "A §9.4 trace over 36 proposals drawn by discovery agents from live "
        "ASX, SEDI and MAR sources refused 34 of them: a 94% false-positive "
        "rate with no true positive among them. A pattern cannot separate a "
        "regulator's name from an issuer's, both being proper nouns. The fence "
        "was rebuilt as a lookup against the security master (P75). The "
        "pattern-only fence had passed every unit test.",
    ),
    (
        "2026-08-27",
        "A legal-form designator suffix implies a firm was named",
        "The branch fired on Rule 16a-8's own heading, 'Trust Holdings and "
        "Transactions'. `Holdings` is a legal-form suffix in a rulebook "
        "heading exactly as it is in a firm's name and the pattern cannot "
        "separate them. Narrowed to a proper-noun-shaped lead absent from a "
        "registered stopword set (P80).",
    ),
    (
        "2026-08-27",
        "The corpus is the material, and the fetch preserved it",
        "Three genuine issuer names, API, BlackBerry and Opera, were refused "
        "once per document on thirteen documents that name no company: they "
        "sat in an HTML comment and a user-agent sniffer in <head>, which the "
        "chrome strip could not reach (P82). Worse, and found only when it was "
        "asked directly: THE RAW FETCHED PAGES WERE NEVER RETAINED. Extraction "
        "was destructive, so `raw_bytes` in the manifest was a number with "
        "nothing behind it and the corpus could be re-derived from nothing. "
        "Both are closed (P84), the second by keeping the pages at "
        "corpora/us/_raw.",
    ),
)


class ReportRefused(RuntimeError):
    """Raised rather than defaulted.  See each call site."""


# ---------------------------------------------------------------------------
# The binding path.
# ---------------------------------------------------------------------------

#: The heading this report writes its binding path under.  Named once because
#: the previous report is parsed back under the same string: a heading that
#: drifted would silently turn every diff into "the previous report has no
#: binding path", which reads as reassuring and is not.
BINDING_PATH_HEADING = "## 1. Binding path"

#: The register's status vocabulary, declared at the top of
#: `docs/OPEN_ITEMS.md` and **exhaustive**.  A cell outside these five is a
#: refusal here and not a widening of this tuple.
#:
#: *Why the reader is strict and the register was normalised instead.* The
#: §13 table once carried `CLOSED for US`, a closure with its scope written
#: into the status, and the first version of this reader admitted it and
#: reported it as qualified. That put the vocabulary in two places, the
#: register's preamble and this tuple, and made the reader the thing that had
#: to be widened whenever a cell was written loosely. **The scope now has a
#: column of its own**, so a partial closure is `PART CLOSED` with a scope
#: beside it, and this tuple is the register's own list rather than a
#: superset of it.
REGISTER_STATUSES = ("OPEN", "BLOCKED", "PROVISIONAL", "PART CLOSED", "CLOSED")

#: The five steps of `docs/OPEN_ITEMS.md`'s *binding path, in order*, and the
#: register cells each is settled by.
#:
#: **The mapping from a step to its cells is declared here; every status is
#: read out of the register.** The declaration is the one judgement in this
#: section and it is printed in the table beside each step, so a reader who
#: disagrees with it can see it rather than infer it. Nothing here is a field
#: the funnel reads at decision time, and nothing here decides anything: the
#: section prints what the register already says, in the order the register
#: already puts it.
#:
#: `("13", ALL_13)` means every numbered row of §13, which is what *populate
#: §13* means and what step 5 waits on.
ALL_13 = "*"
BINDING_PATH: Tuple[Tuple[str, str, Tuple[Tuple[str, str], ...]], ...] = (
    (
        "1",
        "Verify the commission (§13 row 1)",
        (("13", "1"),),
    ),
    (
        "2",
        "Fix the pre-calibration fixings",
        (("13", "22"), ("13", "25")),
    ),
    (
        "3",
        "Settle the §14 governance decisions that gate registration",
        (
            ("14d", "Overlap tolerance θ"),
            ("14d", "δₘᵢₙ floor"),
            ("14d", "Account type, cash or margin"),
        ),
    ),
    (
        "4",
        "Run the trace harness (§9.4) to its stopping rule",
        (("14p", "Trace exercise (§9.4) to its stopping rule"),),
    ),
    (
        "5",
        "Populate §13, hash the parameter object: frozen design 1",
        (("13", ALL_13),),
    ),
)

#: Which markdown table under which heading of the register each key above
#: refers to.  Read by heading rather than by position, so a table moving in
#: the document does not silently rekey the section.
REGISTER_TABLES = {
    "13": "## §13",
    "14d": "## §14: open decisions",
    "14p": "## §14: preconditions to signing the freeze",
}


def register_rows(text: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Every register table with a *Status* column, keyed by its first cell.

    Each row is returned as its whole header-to-cell mapping, so *Status* and
    *Scope* are read by name. Columns are found **by their headers** and never
    by position, so a column inserted before either does not silently start
    reporting the wrong cell. A table with no `Status` header is skipped rather
    than guessed at.
    """

    out: Dict[str, Dict[str, Dict[str, str]]] = {}
    heading = ""
    header: Optional[List[str]] = None
    for line in text.splitlines():
        if line.startswith("## "):
            heading, header = line.strip(), None
            continue
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue                      # the header rule
        if header is None:
            header = cells
            continue
        if "Status" not in header:
            continue
        row = dict(zip(header, cells))
        for key, prefix in REGISTER_TABLES.items():
            if heading.startswith(prefix):
                out.setdefault(key, {})[cells[0]] = row
    return out


def status_token(cell: str) -> str:
    """A register status cell with its markdown emphasis stripped, and nothing else.

    **No splitting and no salvage.** An earlier version took everything up to
    the first colon so that `**OPEN**: the traces of 26 and 27 August ...`
    would yield `OPEN`, which meant the reader silently repaired cells that
    carried a note where a status belongs. The register now keeps its notes in
    a note column, so a cell that is not exactly one of the five is a register
    defect and is reported as one.
    """

    return cell.replace("*", "").replace("`", "").strip()


def is_closed(token: str) -> bool:
    """Whether a status says the thing is done, whole.

    Only `CLOSED`. `PART CLOSED` is a closure over the scope in the scope
    column, and **a step of the binding path is not settled by part of an
    object being settled**: a report that read one as done would say the path
    had moved when the register says it has not.
    """

    return token == "CLOSED"


def binding_path_rows(register: Path) -> List[Tuple[str, str, str, str]]:
    """(step, what it is, status, the register cells it is settled by).

    Refuses rather than defaults. A register that cannot be read, or a row the
    mapping names and the register does not carry, produces a status of
    `CANNOT READ THE REGISTER` with the reason in the evidence cell. **It never
    produces a status of NOT CLOSED by default**, because a step reported as
    outstanding when in fact nothing was read is a refusal wearing a reading's
    clothes.
    """

    try:
        rows = register_rows(Path(register).read_text(encoding="utf-8"))
    except OSError as exc:
        return [
            (n, what, "CANNOT READ THE REGISTER", f"`{register}`: {exc}")
            for n, what, _ in BINDING_PATH
        ]

    out: List[Tuple[str, str, str, str]] = []
    for n, what, cells in BINDING_PATH:
        wanted: List[Tuple[str, Dict[str, str]]] = []
        for table, key in cells:
            table_rows = rows.get(table, {})
            if key == ALL_13:
                wanted += [
                    (f"§13 row {k}", v)
                    for k, v in table_rows.items()
                    if k not in ("n/a", "#")
                ]
            elif key in table_rows:
                label = f"§13 row {key}" if table == "13" else f"§14 {key}"
                wanted.append((label, table_rows[key]))
            else:
                wanted.append((f"{table}:{key}", {}))
        missing = [lab for lab, row in wanted if not row.get("Status")]
        if not wanted or missing:
            out.append((
                n, what, "CANNOT READ THE REGISTER",
                "the mapping names "
                + ", ".join(f"`{m}`" for m in missing or ["nothing"])
                + " and the register does not carry it",
            ))
            continue
        tokens = [
            (lab, status_token(row["Status"]), status_token(row.get("Scope", "")))
            for lab, row in wanted
        ]
        # Strict. A cell outside the register's own five is a register defect,
        # and repairing one here would put the vocabulary in two places and
        # make this file the thing that gets widened.
        unknown = [
            f"{lab}: {t}" for lab, t, _sc in tokens if t not in REGISTER_STATUSES
        ]
        if unknown:
            out.append((
                n, what, "CANNOT READ THE REGISTER",
                "outside the register's declared status vocabulary "
                + f"({', '.join(REGISTER_STATUSES)}): "
                + "; ".join(f"`{u}`" for u in unknown),
            ))
            continue
        def _shown(token: str, scope: str) -> str:
            """The status, with its scope where the register gives it one."""

            return token if scope in ("", "n/a") else f"{token} ({scope})"

        closed = all(is_closed(t) for _, t, _sc in tokens)
        if any(key == ALL_13 for _table, key in cells):
            # Twenty-seven cells printed one by one is a paragraph nobody
            # reads.  Grouped by token instead, which loses no token and so
            # still moves in the diff when any single row's status moves; a
            # bare count would not, and a step that stopped moving in the diff
            # because its evidence was summarised is the failure this whole
            # section exists against.
            groups: Dict[str, List[str]] = {}
            for lab, t, sc in tokens:
                groups.setdefault(_shown(t, sc), []).append(
                    lab.replace("§13 row ", "")
                )
            n_closed = sum(1 for _, t, _sc in tokens if is_closed(t))
            evidence = (
                f"{n_closed} of {len(tokens)} §13 rows closed whole; "
                + "; ".join(
                    f"{t} ({', '.join(labs)})" for t, labs in sorted(groups.items())
                )
            )
        else:
            evidence = "; ".join(
                f"{lab}: {_shown(t, sc)}" for lab, t, sc in tokens
            )
        out.append((n, what, "CLOSED" if closed else "NOT CLOSED", evidence))
    return out


def report_sort_key(p: Path) -> Tuple[str, int]:
    """`<date>_funnel[_NN].md` in the order `next_path` allocates it."""

    stem = p.stem
    on, _, rest = stem.partition("_funnel")
    n = int(rest.lstrip("_")) if rest.lstrip("_").isdigit() else 1
    return on, n


def previous_report(runs_dir: Path) -> Optional[Path]:
    """The latest report already in `runs_dir`, or None if there is none.

    Called at render time, before this run's own file is written, so the latest
    file present is the one this report follows. `next_path` allocates the next
    number rather than overwriting, so the ordering is total.
    """

    try:
        files = [p for p in Path(runs_dir).glob("*_funnel*.md") if p.is_file()]
    except OSError:
        return None
    return max(files, key=report_sort_key) if files else None


def binding_path_of(text: str) -> Dict[str, Tuple[str, str]]:
    """The (status, evidence) of each step in a rendered report, by step.

    Empty for a report written before this section existed, which is a
    different thing from a report in which nothing moved and is reported as
    such rather than as *no movement*.
    """

    parts = text.split(BINDING_PATH_HEADING)
    if len(parts) < 2:
        return {}
    body = parts[1].split("\n## ")[0]
    out: Dict[str, Tuple[str, str]] = {}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        out[cells[0]] = (cells[2].replace("*", ""), cells[3])
    return out


def movement_line(rows, runs_dir: Optional[Path]) -> str:
    """What moved since the previous report in `runs_dir`, by diff.

    **Computed against that file, never asserted.** The three outcomes are
    distinct and the distinction is the point:

    * no previous report: nothing was diffed, and that is said.
    * a previous report with no binding path: nothing was diffed, and that is
      said. It may NOT be reported as no movement, because a comparison that
      did not happen cannot have come out equal.
    * a previous report with one: the diff, or, where it is empty, the words
      **no binding-path movement since <file>** and nothing softer.
    """

    if runs_dir is None:
        return (
            "**No runs directory was given, so nothing was diffed.** This line "
            "states what moved by comparing against the previous report's own "
            "text; with no directory to look in there is no previous report to "
            "compare against and no movement is claimed either way."
        )
    prev = previous_report(Path(runs_dir))
    if prev is None:
        return (
            f"**No previous report in `{runs_dir}`, so nothing was diffed.** "
            "This is the first report written there. Nothing is claimed about "
            "movement, because there is nothing to have moved from."
        )
    was = binding_path_of(prev.read_text(encoding="utf-8"))
    if not was:
        return (
            f"**`{prev.name}` carries no binding path, so nothing was "
            "diffed.** It was written before this section existed. **This is "
            "not the same as no movement**: a comparison that did not happen "
            "cannot have come out equal, and saying otherwise would be this "
            "file asserting the thing it exists to compute."
        )
    moved = [
        (n, was.get(n), (status, evidence))
        for n, _what, status, evidence in rows
        if was.get(n) != (status, evidence)
    ]
    if not moved:
        return f"**no binding-path movement since {prev.name}**"
    out = [f"**Moved since {prev.name}:**", ""]
    for n, before, after in moved:
        if before is None:
            out.append(
                f"- step {n} is new to this report; `{prev.name}` carries no "
                "such step"
            )
            continue
        out.append(
            f"- step {n}: **{before[0]}** to **{after[0]}**"
            + ("" if before[1] == after[1] else
               f"; register cells were *{before[1]}*, now *{after[1]}*")
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Provenance.
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        return ""


def corpus_digest(routes: Sequence[str]) -> List[Tuple[str, str]]:
    """A digest per corpus manifest, so a run names the corpus it read.

    Over the manifest and not the documents: the manifest carries every
    document's name, adopted date, source, retrieved date and both byte counts,
    so a document changing changes it. A corpus route with no manifest is
    reported as having none, never as clean.
    """

    out: List[Tuple[str, str]] = []
    for route in routes:
        man = Path(route) / "_manifest.tsv"
        if not man.exists():
            out.append((route, "no manifest: this corpus cannot be identified"))
            continue
        out.append((route, hashlib.sha256(man.read_bytes()).hexdigest()[:16]))
    return out


# ---------------------------------------------------------------------------
# The queue.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Draft:
    """One directive waiting on a person, and what it waits for."""

    directive_id: str
    event_class: str
    outstanding: Tuple[str, ...]

    @property
    def n_outstanding(self) -> int:
        return len(self.outstanding)


def queue_from_ledger(ledger: Ledger) -> List[Draft]:
    """Every draft, with its outstanding operator inputs, ordered by the count.

    Ascending, so **zero-outstanding drafts come first**: they are the ones
    that need a decision now, and burying them under drafts that cannot move
    would be the report choosing what the operator looks at.
    """

    rows = list(
        ledger.conn.execute(
            "SELECT directive_id, event_class, delta_min, registered_sign, "
            "registered_at FROM directive"
        )
    )
    by_subject: Dict[str, set] = {}
    for r in ledger.conn.execute("SELECT subject_id, code FROM refusal"):
        by_subject.setdefault(r["subject_id"], set()).add(r["code"])

    drafts: List[Draft] = []
    for r in rows:
        seen = by_subject.get(r["directive_id"], set())
        outstanding: List[str] = []
        for name, code in OPERATOR_INPUTS:
            if name == "registered_sign":
                # Read off the record rather than off a refusal, because
                # `screen.register` does not refuse a missing sign. See the
                # report's own note on that.
                if r["registered_sign"] is None:
                    outstanding.append(name)
                continue
            if code in seen:
                outstanding.append(name)
        drafts.append(
            Draft(r["directive_id"], r["event_class"], tuple(outstanding))
        )
    # The count, then the identifier. The identifier ranks nothing; it exists
    # so the order is total and the file is diffable between runs.
    return sorted(drafts, key=lambda d: (d.n_outstanding, d.directive_id))


# ---------------------------------------------------------------------------
# The report.
# ---------------------------------------------------------------------------


@dataclass
class RunReport:
    registration: Registration
    ledger: Ledger
    corpora: List[Tuple[str, str]]
    commit: str
    on: date
    budget_abandoned: int = 0
    #: `docs/OPEN_ITEMS.md`, the register the binding path is read out of, and
    #: `docs/runs/`, the directory the previous report is diffed against. Both
    #: default to None and **None produces a refusal, not a reading**: a report
    #: that guessed at the register's location would print a binding path over
    #: whatever happened to be at a relative path, and a wrong register read
    #: silently is worse than none read loudly.
    register: Optional[Path] = None
    runs_dir: Optional[Path] = None

    # -- sections ----------------------------------------------------------

    def _binding_path(self) -> List[str]:
        """§9.2's first section: the five steps, their status, what moved.

        **First in the report and above the provenance header**, because the
        provenance header answers *under what was this run taken* and this
        answers *has the project moved*. A reader who opens the file for the
        second question should not have to find it under the first. Fourteen
        specification versions, a linter, a reference implementation and a
        discovery layer have been built and the score does not move, so a
        report whose first page is not the score is a report that lets the
        building read as progress.

        **This measures nothing and adds nothing.** The five steps are the
        register's own, in the register's own order; every status is read out
        of `docs/OPEN_ITEMS.md`; the movement line is a diff against the
        previous file in `docs/runs/`. Procedure by §0.6's test: no gate, no
        family, no grammar row, no cost tier, no feed, no sizing input, and no
        field the funnel reads at decision time.
        """

        out = [
            BINDING_PATH_HEADING,
            "",
            "**The register's five steps, in the register's order, with every "
            "status read out of `docs/OPEN_ITEMS.md` rather than stated here.** "
            "The one judgement in this section is which register cells settle "
            "which step, and it is printed in the last column so a reader who "
            "disagrees can see it. A step is **CLOSED** only where every cell "
            "it names reads `CLOSED`: `PART CLOSED` is a closure over the "
            "scope printed beside it and the path is not settled by part of "
            "an object being settled. **A status outside the register's "
            "declared five is refused, not repaired.**",
            "",
        ]
        if self.register is None:
            out += [
                "**No register was given, so no status was read.** The five "
                "steps are named below and none of them carries a status: a "
                "step reported as outstanding when nothing was read would be a "
                "refusal wearing a reading's clothes.",
                "",
                "| step | what it is |",
                "|---|---|",
            ]
            out += [f"| {n} | {what} |" for n, what, _ in BINDING_PATH]
            out += ["", movement_line([], self.runs_dir), ""]
            return out

        rows = binding_path_rows(self.register)
        out += [
            "| step | what it is | status | the register cells it is settled by |",
            "|---|---|---|---|",
        ]
        for n, what, status, evidence in rows:
            out.append(f"| {n} | {what} | **{status}** | {evidence} |")
        closed = sum(1 for _n, _w, st, _e in rows if st == "CLOSED")
        out += [
            "",
            f"**{closed} of {len(rows)} steps closed.** The order is not "
            "negotiable and step 5 creates frozen design 1, which stands at "
            "zero.",
            "",
            "### What moved since the previous report",
            "",
            movement_line(rows, self.runs_dir),
            "",
        ]
        return out

    def _provenance(self) -> List[str]:
        reg = self.registration
        ledger_hashes = sorted(
            {
                r[0]
                for r in self.ledger.conn.execute(
                    "SELECT DISTINCT parameter_hash FROM proposal"
                )
            }
        )
        out = [
            "## 2. Provenance",
            "",
            "| | |",
            "|---|---|",
            f"| registration hash | `{reg.hash()}` |",
            f"| schema fingerprint | `{reg.registered_schema or 'n/a'}` |",
            f"| hash verification | **{reg.hash_verification}** |",
            f"| registered at | {reg.registered_at or 'NOT STAMPED'} |",
            f"| code commit | `{self.commit or 'n/a, not a git checkout'}` |",
            f"| report written | {self.on.isoformat()} |",
        ]
        for route, digest in self.corpora:
            out.append(f"| corpus `{route}` | `{digest}` |")
        out.append("")
        if reg.hash_verification != Registration.VERIFIED:
            out += [
                f"**The registration did not verify: `{reg.hash_verification}`.** "
                "A hash is taken over the dataclass as well as the values, so a "
                "file written under an earlier shape cannot be checked by "
                "recomputation and no verification is claimed for it. Nothing "
                "below is invalid; it is unattested.",
                "",
            ]
        if ledger_hashes and ledger_hashes != [reg.hash()]:
            out += [
                "**The ledger was not written under this registration.** It "
                "carries "
                + ", ".join(f"`{h}`" for h in ledger_hashes)
                + f" and the registration in the tree is `{reg.hash()}`. The "
                "figures below describe the run that happened, under the "
                "parameters that were in force then. `docs/REGISTRATION_HISTORY.md` "
                "is the chain between them. Nothing here is restated under the "
                "current hash, because restating a measurement under parameters "
                "it was not taken under is how a reading acquires a provenance "
                "it never had.",
                "",
            ]
        return out

    def _funnel(self) -> List[str]:
        counts = self.ledger.counts()
        out = [
            "## 3. Intake funnel",
            "",
            f"- proposals raised: **{counts['proposals']}**",
            f"- refusals recorded: **{counts['refusals']}**",
            f"- directives built: **{counts['directives']}**",
            f"- directives registered: **{counts['registered']}**",
            f"- directives promoted: **{counts['promoted']}**",
            f"- abandoned to intake budget: **{self.budget_abandoned}**",
            "",
        ]

        by_surface: Dict[str, Dict[str, int]] = {}
        for r in self.ledger.conn.execute(
            "SELECT surface, code, COUNT(*) n FROM refusal GROUP BY surface, code"
        ):
            by_surface.setdefault(r["surface"], {})[r["code"]] = r["n"]
        out += ["### Refusals per surface, per point", ""]
        if not by_surface:
            out += ["No refusals recorded. Nothing was refused and nothing ran.", ""]
        for surface in sorted(by_surface):
            out += [f"**{surface}**", "", "| point | code | n |", "|---|---|---|"]
            order = {
                "intake": codes.INTAKE_ORDER,
                "observation": codes.OBSERVATION_ORDER,
            }.get(surface, [])
            for code, n in sorted(
                by_surface[surface].items(), key=lambda kv: (-kv[1], kv[0])
            ):
                pos = str(order.index(code) + 1) if code in order else "n/a"
                out.append(f"| {pos} | `{code}` | {n} |")
            out.append("")

        out += self._abort_positions()
        out += self._unexercised()
        return out

    def _abort_positions(self) -> List[str]:
        """§13 row 23, first failures only, by position, SPLIT BY ARM.

        The FIRST refusal per subject on the intake surface, which is what
        fail-fast makes the abort position. Later refusals on the same subject
        are counted in the table above and never here, because a point that
        fires behind an earlier one did not abort anything.

        **Why this is split and no longer pooled (P105, 27 August 2026).** This
        method selected every intake refusal with no filter on ``origin``, so it
        pooled the **agent** arm, which is the thing under test, with the
        **random-mechanism control** arm, which exists in order to be compared
        against it.  Pooling the control into the treatment destroys the
        comparison the control arm is for.

        It is the third instance of one error.  P77 and P79 found §13 row 21
        pooling a drawn arm with an authored one; P95 found row 23 doing the
        same; this one differs in being **in code**, rendered from the ledger on
        every run rather than published once in a document.

        *The cost of the repair, stated:* a split distribution has smaller
        denominators and each arm's reading is correspondingly weaker.  That is
        the correct trade, because a pooled figure over two arms with disjoint
        failure positions describes neither of them.
        """

        first: Dict[str, str] = {}
        arm_of: Dict[str, str] = {}
        for r in self.ledger.conn.execute(
            "SELECT r.subject_id, r.code, p.origin FROM refusal r "
            "LEFT JOIN proposal p ON p.subject_id = r.subject_id "
            "WHERE r.surface = 'intake' ORDER BY r.id"
        ):
            first.setdefault(r["subject_id"], r["code"])
            # An origin the ledger does not carry is recorded as unattributed
            # rather than folded into either arm: a subject whose arm is unknown
            # is not evidence about either one.
            arm_of.setdefault(r["subject_id"], r["origin"] or "unattributed")

        sized = {
            r["origin"]: r["n"]
            for r in self.ledger.conn.execute(
                "SELECT origin, COUNT(*) n FROM proposal GROUP BY origin"
            )
        }
        # Every arm that RAISED a subject gets a column, refused or not: an arm
        # that raised twelve and lost none is a reading, and a column of zeros
        # is how it is reported.  The fallback column exists so that the twelve
        # positions always print with a count beside them, including on a run
        # that refused nothing at all.
        arms = sorted({arm_of[s] for s in first} | set(sized)) or ["n"]
        tallies: Dict[str, Dict[str, int]] = {a: {} for a in arms}
        for subject, code in first.items():
            arm = tallies[arm_of[subject]]
            arm[code] = arm.get(code, 0) + 1
        pooled: Dict[str, int] = {}
        for code in first.values():
            pooled[code] = pooled.get(code, 0) + 1

        out = [
            "### Abort-position distribution (§13 row 23), BY ARM",
            "",
            "First failures only, on the intake surface. A point firing behind "
            "an earlier one aborted nothing and is counted in the table above "
            "instead.",
            "",
            "**Split by `origin`, and never pooled.** The control arm exists to "
            "be compared against the agent arm, so a distribution that adds "
            "them together describes neither. This is the same correction P79 "
            "and P95 made to §13 rows 21 and 23, made here to the code that "
            "renders them.",
            "",
        ]
        header = "| pos | point | " + " | ".join(arms) + " |"
        out += [header, "|---|---|" + "---|" * len(arms)]
        deepest = 0
        for pos, code in enumerate(codes.INTAKE_ORDER, start=1):
            cells = [tallies[a].get(code, 0) for a in arms]
            if any(cells):
                deepest = max(deepest, pos)
            out.append(
                f"| {pos} | `{code}` | " + " | ".join(str(c) for c in cells) + " |"
            )
        out.append("")
        for arm in arms:
            n = sum(tallies[arm].values())
            raised = sized.get(arm)
            rate = (
                f"{n}/{raised} = **{100.0 * n / raised:.1f}%**"
                if raised
                else f"{n}, denominator unavailable"
            )
            out.append(f"- **{arm}**: intake kill rate {rate}")
        out += [
            "",
            f"Deepest position reached by a failure, any arm: **{deepest} of "
            f"{len(codes.INTAKE_ORDER)}**."
            if deepest
            else "No intake failure recorded, so no position was reached.",
            "",
            "**The pooled figure, retained and NOT a reading.** "
            + ", ".join(
                f"`{c}` {n}" for c, n in sorted(pooled.items(), key=lambda kv: -kv[1])
            )
            + f", total {sum(pooled.values())}. It is printed so that a reader "
            "comparing this report with one published before P105 can see what "
            "moved, and for no other purpose.",
            "",
        ]
        return out + self._budget_note()

    def _budget_note(self) -> List[str]:
        """The abandonment count, printed beside row 23's distribution.

        Kept as its own method since P105 so that both exits from
        `_abort_positions` render it: a run that refused nothing and abandoned
        several subjects is precisely the run whose silence would mislead.
        """

        if not self.budget_abandoned:
            return []
        return [
            f"**Beside this distribution and not inside it: "
            f"{self.budget_abandoned} subject(s) abandoned to the intake "
            "budget.** A subject that ran out of time did not fail the "
            "point it was standing on, and counting it there would put a "
            "clock's verdict in a check's column.",
            "",
        ]

    def _unexercised(self) -> List[str]:
        exercised = {
            r["code"]
            for r in self.ledger.conn.execute(
                "SELECT DISTINCT code FROM refusal WHERE surface = 'intake'"
            )
        }
        never = [c for c in codes.INTAKE_ORDER if c not in exercised]
        out = ["### Intake points not exercised by this run", ""]
        if not never:
            out += ["None: every intake point fired at least once.", ""]
            return out
        out += [
            f"**{len(never)} of {len(codes.INTAKE_ORDER)}**, named rather than "
            "counted, because a point nothing reached is a branch nothing "
            "tested and the count alone does not say which:",
            "",
        ]
        out += [f"- `{c}` (position {codes.INTAKE_ORDER.index(c) + 1})" for c in never]
        out.append("")
        return out

    def _fences(self) -> List[str]:
        by_code: Dict[str, int] = dict(self.ledger.code_distribution())
        queries = self.ledger.counts()["queries"]
        out = [
            "## 4. Fence report",
            "",
            "Four fences, four units. They are not summed: an import breach and "
            "an entity refusal are not two of the same thing, and a total over "
            "them would be a number with no denominator and no meaning.",
            "",
            "| fence | unit | reading |",
            "|---|---|---|",
            f"| import (§3.7.2) | breaches | "
            f"{by_code.get('import_fence_breach', 0)} |",
            f"| query (§3.7.4) | entries logged | {queries} |",
            f"| entity (§3.7.3) | proposals refused | "
            f"{by_code.get('proposal_names_entity', 0)} |",
            f"| authority (§3.7.6) | schema overreaches | "
            f"{by_code.get('agent_overreached_schema', 0)} |",
            "",
            "### The entity fence, in two arms (§13 rows 21a and 21b)",
            "",
            "**The arms are of two kinds and are never combined.** Reporting "
            "them as one was itself a defect (P77, P79), and the understatement "
            "was largest exactly where the arms were least balanced.",
            "",
            "| arm | kind | reading |",
            "|---|---|---|",
            "| drawn class-level (21a) | a rate, with an interval | "
            "**0 events in 36 trials; 95% upper bound approximately 8.3%** by "
            "the rule of three |",
            "| authored probes (21b) | coverage, never a rate | "
            "**5 of 6 routes closed**; the open one is a title-case bare "
            "ticker |",
            "",
            "*The drawn arm is not 0%.* Zero events does not estimate zero: a "
            "fence refusing one clean proposal in twenty produces this same "
            "reading better than one time in six. Row 21a is **BLOCKED** on the "
            "design segment, the tolerance being set by how much funnel depth "
            "§7.1 can lose before it loses power.",
            "",
            "*The probe arm carries no percentage.* Six probes chosen one per "
            "named route are not a sample, and doubling the set to twelve routes "
            "would halve any percentage whilst leaving the fence untouched. Row "
            "21b is **PROVISIONAL**, unblocked by the operator reading the six.",
            "",
        ]
        return out

    def _queue(self) -> List[str]:
        drafts = queue_from_ledger(self.ledger)
        ready = [d for d in drafts if d.n_outstanding == 0]
        waiting = [d for d in drafts if d.n_outstanding]
        out = [
            "## 5. The queue",
            "",
            "**Ordered by how many operator inputs each draft is still missing, "
            "ascending, and by nothing else.** Ties break on the directive "
            "identifier, which ranks nothing. There is no merit column, no "
            "severity, no score and no recency: any of them would be this file "
            "telling the operator which of their own decisions matters most, "
            "which is the clerk becoming an analyst.",
            "",
        ]
        if not drafts:
            out += ["No drafts. Nothing is waiting on anyone.", ""]
            return out

        out += [
            f"### Nothing outstanding: {len(ready)} draft(s). "
            "**These need a decision now.**",
            "",
        ]
        if ready:
            out += ["| directive | class |", "|---|---|"]
            out += [f"| `{d.directive_id}` | {d.event_class} |" for d in ready]
        else:
            out += [
                "None. Every draft is still missing at least one operator input, "
                "which is the scanner's designed steady state and not a fault "
                "in it.",
            ]
        out += ["", f"### Waiting: {len(waiting)} draft(s)", ""]
        if waiting:
            out += ["| outstanding | directive | class | awaiting |",
                    "|---|---|---|---|"]
            for d in waiting:
                out.append(
                    f"| {d.n_outstanding} | `{d.directive_id}` | {d.event_class} "
                    f"| {', '.join(f'`{o}`' for o in d.outstanding)} |"
                )
        out += [
            "",
            "**`registered_sign` is read off the directive and not off a "
            "refusal, because `screen.register` does not refuse a missing "
            "sign.** It refuses on `delta_min`, the pre-mortem and the "
            "literature search, and lets a directive register with no sign. "
            "CLAUDE.md names the sign among the four things nothing "
            "machine-raised may supply, so the queue shows it outstanding; the "
            "gap between showing it and enforcing it is stated here rather than "
            "closed by this file, a report being the wrong place to add a "
            "refusal.",
            "",
        ]
        return out

    def _control_arm(self) -> List[str]:
        reg = self.registration
        n_control = int(
            self.ledger.conn.execute(
                "SELECT COUNT(*) FROM proposal WHERE origin = 'random_control'"
            ).fetchone()[0]
        )
        n_agent = int(
            self.ledger.conn.execute(
                "SELECT COUNT(*) FROM proposal WHERE origin = 'agent'"
            ).fetchone()[0]
        )
        n_min = reg.control_arm_n_min
        reached = n_min is not None and min(n_agent, n_control) >= n_min
        out = [
            "## 6. Control arm (§13 rows 19 and 20)",
            "",
            "| | |",
            "|---|---|",
            f"| registered separation δ | {reg.control_arm_delta} "
            f"{reg.control_arm_delta_units} |",
            f"| registered *n*ₘᵢₙ per arm | {n_min} |",
            f"| registered ratio / seed | {reg.control_arm_ratio} / "
            f"{reg.control_arm_seed} |",
            f"| agent arm, n | {n_agent} |",
            f"| control arm, n | {n_control} |",
            f"| *n*ₘᵢₙ reached | {'yes' if reached else 'NO'} |",
            "| measured separation | **not measured** |",
            "| **verdict** | **NOT YET RUN** |",
            "",
            "**Not yet run, which is neither refuted nor undetermined.** The "
            "arms are drawn and counted; nothing has been scored against either, "
            "because scoring needs a design segment and there is none. "
            "`undetermined_at_budget` is the verdict for a measurement that ran "
            "and could not separate the arms at the sample it had, and claiming "
            "it here would say a measurement had happened.",
            "",
            f"The kill criterion was committed **blind**, on 26 August 2026, "
            f"before any archive exists: δ = {reg.control_arm_delta} "
            f"{reg.control_arm_delta_units}, *n*ₘᵢₙ = {n_min}, ratio "
            f"{reg.control_arm_ratio}, seed {reg.control_arm_seed}. Those four "
            "values are identical in every row of "
            "`docs/REGISTRATION_HISTORY.md`, and "
            "`test_control_arm_values_unchanged_across_restamps` is what says "
            "so rather than this sentence.",
            "",
        ]
        return out

    def _coverage(self) -> List[str]:
        emitted = set(self.ledger.emitted_codes())
        never = sorted(set(codes.ALL_CODES) - emitted)
        out = [
            "## 7. Reason-code coverage (§9.4)",
            "",
            f"- codes defined: **{len(codes.ALL_CODES)}**",
            f"- codes emitted by this run: **{len(emitted)}**",
            f"- defined but never emitted: **{len(never)}**",
            "",
            "**A low figure on a single run is expected and is not a defect.** "
            "One sweep exercises a handful of branches; the suite exercises all "
            "of them deliberately, and `test_every_defined_code_is_emitted` is "
            "what holds the registry to that. What this section is for is the "
            "list, not the ratio.",
            "",
        ]
        if never:
            out += ["### Untested branches on this run", ""]
            out += [f"- `{c}`" for c in never]
            out.append("")
        return out

    def _refutations(self) -> List[str]:
        out = [
            "## 8. Refutations",
            "",
            "**Rules this project's own instruments have falsified.** Kept here "
            "because a report whose refutation section is empty teaches its "
            "reader that the section is decorative, and because the product is "
            "the ledger of what was withheld and why. Each of these was a rule "
            "believed at the time it was written.",
            "",
        ]
        for when, rule, how in STANDING_REFUTATIONS:
            out += [f"**{when}: {rule}**", "", how, ""]
        return out

    def _not_measured(self) -> List[str]:
        return [
            "## 9. Not measured",
            "",
            "Stated explicitly, because a section absent from a report reads as "
            "a question nobody asked.",
            "",
            "- **Returns, of any kind.** No design segment, no backtest, no "
            "trade. Zero frozen designs.",
            "- **§7.1's funnel-depth association and §7.5's placebo.** Both "
            "unrun, which is why §0.6 is armed.",
            "- **The control arm's separation.** Arms drawn and counted, "
            "nothing scored.",
            "- **§13 row 1, the broker commission.** Unverified, and the most "
            "leveraged number in the paper. The clip stays £2,500 and the "
            "reachability figures stand until it verifies.",
            "- **The fence's false-positive rate at any useful precision.** Row "
            "21a is blocked; what exists is an upper bound on 36 trials.",
            "- **Whether the clerk's labels are the operator's.** Row 21a and "
            "21b both read against `model_clerk` labels. "
            "`python -m fntn.scanner ratify-draw` puts twelve of the "
            "thirty-six in front of a person with the labels withheld.",
            "- **Anything at all about the market.** This layer runs at zero "
            "capital and produces no trading signal.",
            "",
        ]

    # -- assembly ----------------------------------------------------------

    def render(self) -> str:
        head = [
            f"# Run report, {self.on.isoformat()}",
            "",
            "Rendered from the ledger, the registration and the code registry. "
            "**Nothing here is measured by this file**: where a record does not "
            "exist the section says so rather than being omitted.",
            "",
        ]
        body: List[str] = []
        for section in (
            self._binding_path,
            self._provenance,
            self._funnel,
            self._fences,
            self._queue,
            self._control_arm,
            self._coverage,
            self._refutations,
            self._not_measured,
        ):
            body += section()
        return "\n".join(head + body).rstrip() + "\n"


def next_path(directory: Path, on: date) -> Path:
    """The next unused file for this date.  Never an overwrite.

    One file per run, and a run's report is not editable by running again: a
    second run on the same day takes the next number rather than replacing what
    the first one recorded.
    """

    directory.mkdir(parents=True, exist_ok=True)
    base = directory / f"{on.isoformat()}_funnel.md"
    if not base.exists():
        return base
    n = 2
    while (directory / f"{on.isoformat()}_funnel_{n:02d}.md").exists():
        n += 1
    return directory / f"{on.isoformat()}_funnel_{n:02d}.md"
