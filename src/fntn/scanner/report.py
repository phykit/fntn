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

**The queue's ordering is the one design decision in here, and it is a
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

    # -- sections ----------------------------------------------------------

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
            "## 1. Provenance",
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
            "## 2. Intake funnel",
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
        """§13 row 23, first failures only, by position.

        The FIRST refusal per subject on the intake surface, which is what
        fail-fast makes the abort position. Later refusals on the same subject
        are counted in the table above and never here, because a point that
        fires behind an earlier one did not abort anything.
        """

        first: Dict[str, str] = {}
        for r in self.ledger.conn.execute(
            "SELECT subject_id, code FROM refusal WHERE surface = 'intake' "
            "ORDER BY id"
        ):
            first.setdefault(r["subject_id"], r["code"])
        tally: Dict[str, int] = {}
        for code in first.values():
            tally[code] = tally.get(code, 0) + 1

        out = [
            "### Abort-position distribution (§13 row 23)",
            "",
            "First failures only, on the intake surface. A point firing behind "
            "an earlier one aborted nothing and is counted in the table above "
            "instead.",
            "",
            "| pos | point | first failures |",
            "|---|---|---|",
        ]
        deepest = 0
        for pos, code in enumerate(codes.INTAKE_ORDER, start=1):
            n = tally.get(code, 0)
            if n:
                deepest = max(deepest, pos)
            out.append(f"| {pos} | `{code}` | {n} |")
        out += [
            "",
            f"Deepest position reached by a failure: **{deepest} of "
            f"{len(codes.INTAKE_ORDER)}**."
            if deepest
            else "No intake failure recorded, so no position was reached.",
            "",
        ]
        if self.budget_abandoned:
            out += [
                f"**Beside this distribution and not inside it: "
                f"{self.budget_abandoned} subject(s) abandoned to the intake "
                "budget.** A subject that ran out of time did not fail the "
                "point it was standing on, and counting it there would put a "
                "clock's verdict in a check's column.",
                "",
            ]
        return out

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
            "## 3. Fence report",
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
            "## 4. The queue",
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
            "## 5. Control arm (§13 rows 19 and 20)",
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
            "## 6. Reason-code coverage (§9.4)",
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
            "## 7. Refutations",
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
            "## 8. Not measured",
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
