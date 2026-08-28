"""Command line: register, then check, then sweep. In that order, enforced.

    python -m fntn.scanner init      > writes a blank registration form
    python -m fntn.scanner check     > says exactly what is still missing
    python -m fntn.scanner trace     > tests the machinery, evidentially inert
    python -m fntn.scanner sweep     > runs, only if the form is complete

`sweep` refuses on an incomplete registration and names every gap. That refusal
is the point of the command existing: the alternative is a sweep that runs on
whatever happened to be filled in, and a directive raised under a partial
registration cannot be attributed to anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from . import summaries
from .clients import AnthropicClient, ClientRefusal, TranscriptClient
from .discovery import Corpus as SweepCorpus, GridCell
from .fences import QueryFence
from .ledger import Ledger
from .markets import MARKETS, render as render_markets, resolve
from .master import SecurityMaster
from .corpusio import uncommitted_routes, corpus_documents
from .params import Registration, RegistrationIncomplete
from .records import Partition, ScoringMode, SegmentSpan
from .run import ScanConfig, scan
from .segment import SegmentPolicy
from .trace import TraceHarness, load_labelled
from .trace_filings import ResponseNotTheDocument

DEFAULT_REG = "discovery_registration.json"


def _load_master(reg: Registration) -> tuple:
    """Load every master file. Returns (master, problems).

    A missing or unreadable file is a refusal with the file named, not a
    traceback: the template prefills a path per market and most of them will
    not exist yet, which is an ordinary state rather than an error.
    """

    # The registered lexicon, not the module seed: the loader filters the
    # ticker set against it, so a master loaded under a different list is a
    # master the run's hash does not describe.
    master = SecurityMaster(lexicon=frozenset(reg.lexicon))
    problems: List[str] = []
    for spec in reg.security_master_files:
        # "path" or "path:market" or "path:market:listed_total"
        parts = spec.split(":")
        path, market, total = parts[0], None, None
        if len(parts) > 1 and parts[1]:
            market = parts[1]
        if len(parts) > 2 and parts[2] and parts[2] != "<listed_total>":
            total = int(parts[2])
        # The SEC publishes JSON, every exchange publishes CSV. Dispatch on the
        # file rather than making the operator remember which loader to name.
        try:
            if path.lower().endswith(".json"):
                master.load_sec_tickers(path, market=market or "US", listed_total=total)
            else:
                master.load_csv(path, market=market, listed_total=total)
        except FileNotFoundError:
            problems.append(
                f"{path}: not found, so {market or 'its market'} has no master "
                "and is not readable for discovery"
            )
        except (OSError, ValueError) as exc:
            problems.append(f"{path}: {exc}")
    return master, problems


def cmd_init(args) -> int:
    p = Path(args.registration)
    if p.exists() and not args.force:
        print(f"{p} exists. Use --force to overwrite, but note that overwriting")
        print("a stamped registration destroys the timestamp its standing rests on.")
        return 1
    reg = Registration.blank()
    reg.save(p)
    print(f"wrote {p}")
    print()
    print("Fill in every field, then run `check`. The six that only you can")
    print("supply, and why each is yours rather than the machine's:")
    print()
    print("  control_arm_delta    the separation below which the discovery layer")
    print("                       is refuted. Committed before you know whether")
    print("                       the answer flatters you.")
    print("  control_arm_n_min    observations per arm below which the verdict is")
    print("                       undetermined rather than a quiet pass.")
    print("  control_arm_ratio    drawn mechanisms per proposed one. Above zero.")
    print("  control_arm_seed     any integer, recorded, never redrawn.")
    print("  theta                pairwise design-segment overlap tolerance.")
    print("  delta_min_floor      smallest effect worth a session of the segment.")
    return 0


def cmd_markets(args) -> int:
    print(render_markets())
    print()
    print("A corpus from an in-universe market cannot provide cross_market:")
    print("discovery and evaluation would share a price path. Use pre_archive")
    print("(material predating the archive) or forward_only (scored after")
    print("registered_at). The CLI refuses the other way round.")
    return 0


def cmd_template(args) -> int:
    """Write a registration prefilled for every known market."""

    from .params import Corpus as RegCorpus, DiscoverableClass, Registration

    reg = Registration.blank()
    reg.corpora = [
        RegCorpus(
            corpus_id=m.code.lower(),
            market=m.code,
            partition="external",
            retrieval_route=f"./corpora/{m.code.lower()}",
            scoring_mode=m.construction.value,
        )
        for m in MARKETS.values()
    ]
    reg.discoverable_classes = [
        DiscoverableClass("insider_dealing", external_markets="US, UK, AU, EU, NZ"),
        DiscoverableClass("major_holdings_change", external_markets="US, UK, AU, EU"),
        DiscoverableClass("buyback", external_markets="UK, AU, EU"),
        DiscoverableClass("earnings_event", external_markets="US, UK, AU, EU, NZ"),
    ]
    reg.security_master_files = [
        f"./master/{m.code.lower()}.json:{m.code}" if m.master_loader == "load_sec_tickers"
        else f"./master/{m.code.lower()}.csv:{m.code}:<listed_total>"
        for m in MARKETS.values()
    ]
    reg.rationale = "Why these values and not others. Replace this line."
    p = Path(args.registration)
    if p.exists() and not args.force:
        print(f"{p} exists. Use --force to overwrite.")
        return 1
    reg.save(p)
    print(f"wrote {p}, prefilled for {len(MARKETS)} markets")
    print()
    print("Still yours to supply: control_arm_delta, control_arm_n_min,")
    print("control_arm_ratio, control_arm_seed, theta, delta_min_floor,")
    print("registered_at, registered_by, and a listed_total per CSV market.")
    print()
    print("Master files to fetch:")
    for m in MARKETS.values():
        print(f"  {m.code}: {m.master_source}")
    return 0


def cmd_check(args) -> int:
    try:
        reg = Registration.load(args.registration)
    except FileNotFoundError:
        print(f"{args.registration} not found. Run `init` first.")
        return 1
    print(reg.render())
    gaps = reg.missing()
    if reg.security_master_files:
        print()
        master, problems = _load_master(reg)
        print(master.render(floor=reg.master_coverage_floor))
        for prob in problems:
            print(f"    unreadable: {prob}")
        if not master.per_market:
            gaps.append("no security master could be loaded (§13 row 25)")
    return 1 if gaps else 0


def cmd_trace(args) -> int:
    """Run the §9.4 trace harness against the registered configuration.

    Separate from `sweep` because the two are different acts. A sweep is the
    layer running; a trace is the layer being tested, full panel on every
    subject, stamped NON_EVIDENTIARY, refusing to register or admit. Running the
    trace through `sweep` would put subjects with no registered kill criterion
    into the same ledger as subjects that have one, and nothing downstream could
    then tell them apart.
    """

    try:
        reg = Registration.load(args.registration)
    except FileNotFoundError:
        print(f"{args.registration} not found. Run `init` first.")
        return 1

    master, problems = _load_master(reg)
    for prob in problems:
        print(f"master: {prob}")
    if not master.per_market:
        print()
        print("No security master loaded, so the entity fence has no binding")
        print("layer. The trace would measure a fence that is not running.")
        return 5

    try:
        labelled = load_labelled(args.labelled)
    except FileNotFoundError:
        print(f"{args.labelled} not found.")
        print()
        print("The labelled set is the denominator of the §13 row 21 audit and")
        print("it lives in the tree, not in the shell that invoked the harness.")
        print("A fence error rate measured against labels nobody can read back")
        print("is an assertion about a fence, not a measurement of one.")
        return 6

    exclusivity = {c.event_class: reg.default_scoring_mode
                   for c in reg.discoverable_classes}
    harness = TraceHarness(
        exclusivity_available=exclusivity,
        entity_fence=master.as_fence(
            lexicon=frozenset(reg.lexicon),
            stopwords=frozenset(reg.rulebook_stopwords),
        ),
    )
    print(f"registration {reg.hash()} stamped {reg.registered_at}")
    print(master.render(floor=reg.master_coverage_floor))
    print(f"labelled set : {args.labelled}, {len(labelled)} subjects, "
          f"labellers {sorted({l.labeller for l in labelled})}")
    print()
    report = harness.run(labelled, QueryFence())
    print(report.render(harness.ledger))
    harness.close()
    return 0


def cmd_ratify_draw(args) -> int:
    """Write the operator's ratification worksheet, clerk labels withheld.

    Procedure, not apparatus: it produces a document for a person and no verdict
    for a machine, and nothing downstream reads what it writes.
    """

    from . import ratify

    try:
        reg = Registration.load(args.registration)
    except FileNotFoundError:
        print(f"{args.registration} not found. Run `init` first.")
        return 1
    if reg.control_arm_seed is None:
        print("no registered seed. The draw is unchoosable only because it comes")
        print("from the registration; without one it would come from whoever ran")
        print("this, which is the thing the draw exists to prevent.")
        return 2

    labelled = load_labelled(args.labelled)
    on = date.fromisoformat(args.on) if args.on else date.today()
    out = Path(args.out or f"docs/ratification_draw_{on.isoformat()}.md")
    if out.exists() and not args.overwrite:
        print(f"{out} exists. Refusing to overwrite a worksheet that may already")
        print("carry an operator's labels. Pass --overwrite to replace it, or")
        print("--out to write elsewhere.")
        return 3
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = ratify.render_draw(labelled, reg.control_arm_seed, reg.hash(), on)
    except ratify.RatificationRefused as exc:
        print(f"refused: {exc}")
        return 4
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")
    print(f"  registration {reg.hash()}, seed {reg.control_arm_seed}")
    print(f"  {ratify.DRAW_N} drawn-arm subjects, labels WITHHELD")
    print("  6 authored probes, shown in full")
    print()
    print("One disagreement in twelve refutes the clerk's labels for the whole")
    print("drawn arm. That rule is in the file, above the subjects, and it was")
    print("written before any label was revealed.")
    return 0


def cmd_ratify_reveal(args) -> int:
    """Reveal the clerk labels and report agreement as a count."""

    from . import ratify

    try:
        reg = Registration.load(args.registration)
    except FileNotFoundError:
        print(f"{args.registration} not found.")
        return 1
    labelled = load_labelled(args.labelled)

    raw = json.loads(Path(args.labels).read_text(encoding="utf-8"))
    operator = {
        k: (v == "class_level" if isinstance(v, str) else bool(v))
        for k, v in raw.items()
    }
    try:
        result = ratify.reveal(labelled, reg.control_arm_seed, operator)
    except ratify.RatificationRefused as exc:
        print(f"refused: {exc}")
        return 4
    print(result.render())
    return 0 if not result.refutes else 5


def cmd_report(args) -> int:
    """Write the run report. Renders the ledger; measures nothing."""

    from . import report as report_mod

    try:
        reg = Registration.load(args.registration)
    except FileNotFoundError:
        print(f"{args.registration} not found. Run `init` first.")
        return 1

    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        print(f"{ledger_path} not found. A run report renders a ledger, and")
        print("there is no ledger. Run `sweep` first, or pass --ledger.")
        return 2

    ledger = Ledger(ledger_path, parameter_hash=reg.hash())
    on = date.fromisoformat(args.on) if args.on else date.today()
    rep = report_mod.RunReport(
        registration=reg,
        ledger=ledger,
        corpora=report_mod.corpus_digest([c.retrieval_route for c in reg.corpora]),
        commit=report_mod._git("rev-parse", "HEAD")[:12],
        on=on,
        # Read off the ledger, not off a flag. The count is a record of what
        # the run did, and a report that took it from the command line would
        # print whatever the caller said.
        budget_abandoned=(
            args.budget_abandoned
            if args.budget_abandoned is not None
            else ledger.budget_abandoned()
        ),
        # Both read at render time and neither guessed at. A missing register
        # produces a section that says no status was read, never a section of
        # statuses read from somewhere else.
        register=Path(args.open_items),
        runs_dir=Path(args.dir),
    )
    out = Path(args.out) if args.out else report_mod.next_path(
        Path(args.dir), on
    )
    if out.exists():
        print(f"{out} exists. Reports are append-only, one file per run: a")
        print("second run takes the next number rather than replacing the")
        print("record the first one made.")
        ledger.close()
        return 3
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rep.render(), encoding="utf-8")
    ledger.close()
    print(f"wrote {out}")
    print(f"  registration {reg.hash()} ({reg.hash_verification})")
    print(f"  abandoned to intake budget: {rep.budget_abandoned}")
    return 0


def cmd_trace_filings(args) -> int:
    """Fetch one block of Form 4 filings into the fenced trace corpus (§9.4).

    Refuses before writing anything if SEC_CONTACT is unset. The corpus is
    fenced: no registration route may resolve to it, the sweep's loader will
    not read it, and discovery.py's import closure does not name it.
    """

    from . import trace_filings as tfm

    on = date.fromisoformat(args.on) if args.on else date.today()
    print(f"§9.4 trace corpus: one block of {tfm.BLOCK_SIZE} "
          f"{tfm.FORM_TYPE} Item {tfm.TARGET_ITEM} filings")
    print(f"  item    : {tfm.TARGET_ITEM_TITLE}")
    print( "            RE-POINTED from Form 4 (§12.1 P126). Item 2.02 is the")
    print( "            only candidate exercising extraction against PROSE,")
    print( "            which is the one place a model still touches a number.")
    print(f"  index   : {tfm.daily_index_url(on)}")
    print(f"  corpus  : {tfm.CORPUS_ROOT}  (fenced, {tfm.NON_EVIDENTIARY})")
    print(f"  block   : {tfm.BLOCK_SIZE}, because §9.4's stopping rule computes")
    print( "            the marginal defect rate PER HUNDRED ITEMS. Two")
    print( "            consecutive blocks below threshold are required, so one")
    print( "            block cannot discharge it and does not claim to.")
    print()
    try:
        filings = tfm.fetch_block(on, limit=args.limit or tfm.BLOCK_SIZE)
    except tfm.TraceCorpusRefused as exc:
        print("REFUSED, and nothing was fetched or written:")
        print()
        print(exc)
        return 4
    except tfm.ResponseNotTheDocument as exc:
        print("THE RESPONSE WAS NOT THE DOCUMENT. Reported, not worked around:")
        print()
        print(exc)
        return 5
    manifest = tfm.write_manifest(filings)
    print(f"fetched {len(filings)} filings; manifest {manifest}")
    print(f"  examined {filings[0].scanned} {tfm.FORM_TYPE} filings of "
          f"{filings[0].candidates} on the day")
    wanted = args.limit or tfm.BLOCK_SIZE
    if len(filings) < wanted:
        print()
        print(f"  SHORT OF A BLOCK: {len(filings)} against {wanted}. The day")
        print( "  did not carry enough Item 2.02 filings, which is a fact about")
        print( "  the day and not a fetch failure. §9.4's stopping rule reads a")
        print( "  defect rate PER HUNDRED, so a short block cannot be read as a")
        print( "  block: take further days until the hundred is made, and record")
        print( "  every date taken. Nothing here is retried against a date")
        print( "  chosen to produce a result.")
    return 0


class CostCeilingExceeded(RuntimeError):
    """The projected cost of the whole sweep exceeded the stated ceiling.

    Raised from inside the gather loop so that nothing is registered, nothing
    is drawn and nothing reaches the ledger. **A stop, never a truncation:** a
    sweep over one family of three, reported as a sweep, would put a partial
    population under §7.1's headline with nothing on the record saying so.
    """


def _cost_guard(client, ceiling_usd: float):
    """Measure what the first corpus cost and project the whole sweep.

    **Why a projection from one family and not a token count up front.** The
    input side could be counted before calling, but the output side cannot: how
    many proposals the clerk emits is the thing being measured. One family is
    the cheapest real observation of both halves.

    **What the projection assumes, stated because it is an assumption.** That
    the remaining families cost about what the first one did. They differ in
    document count and length, so this is an order-of-magnitude guard and is
    reported as one. It is deliberately the crude version: a guard that needed
    calibrating would need a sweep to calibrate it.

    **The control arm adds nothing to the projection, and that is measured
    rather than assumed:** `draw_control_mechanisms` takes the grid, a count
    and the registered seed, and takes no client. It makes no model call, so
    its marginal cost is zero.
    """

    if ceiling_usd <= 0:
        return None

    def guard(index: int, total: int) -> None:
        spend = client.spend()
        if index != 0 or total <= 1:
            # Every family is reported, cumulatively, because a per-family
            # figure costs nothing to print and the alternative is a total
            # nobody can attribute. Only the FIRST one projects and enforces.
            print()
            print(spend.render(f"cumulative after family {index + 1} of {total}"))
            return
        print()
        print("COST GUARD, after the first family and before the rest.")
        print(spend.render("measured"))
        if spend.usd is None:
            raise CostCeilingExceeded(
                f"the cost of the first family cannot be scored: {spend.model!r} "
                "is not in the price table. Refusing to project from a number "
                "that does not exist, and refusing to treat an unknown rate as "
                "a small one."
            )
        projected = spend.usd * total
        print(f"  families                 : {total}")
        print(f"  PROJECTED for all {total}      : USD {projected:.4f}")
        print( "  control arm              : USD 0.0000, and this is measured,")
        print( "                             not assumed: the draw takes the grid")
        print( "                             and the registered seed and makes no")
        print( "                             model call.")
        print(f"  ceiling                  : USD {ceiling_usd:.2f}")
        if projected > ceiling_usd:
            raise CostCeilingExceeded(
                f"PROJECTED USD {projected:.4f} for {total} families exceeds the "
                f"ceiling of USD {ceiling_usd:.2f}, projected from USD "
                f"{spend.usd:.4f} measured on the first. Nothing further was "
                "called."
            )
        print("  within the ceiling; continuing.")
        print()

    return guard


def cmd_delisting_register(args) -> int:
    """Build the delisting register (§0.7, survivorship).

    **The span defaults to the registration's `archive_opens` and not to a date
    chosen here.** A register covering a different span from the archive it
    bounds would give a coverage fraction over the wrong denominator, which is
    a worse failure than having none.
    """

    from ..data import delistings as dl

    if args.opens:
        opens = date.fromisoformat(args.opens)
    else:
        try:
            reg = Registration.load(args.registration)
        except FileNotFoundError:
            print(f"{args.registration} not found, and --opens was not given.")
            print("Refusing to choose a span: the register's span is the")
            print("archive's, and reading it from anywhere else would bound")
            print("the wrong population.")
            return 1
        if not reg.archive_opens:
            print("archive_opens is not registered and --opens was not given.")
            print("Refused rather than defaulted (§13 pre-calibration fixing).")
            return 2
        opens = date.fromisoformat(reg.archive_opens)
    closes = date.fromisoformat(args.closes) if args.closes else date.today()

    print("Delisting register (§0.7 survivorship, free route)")
    print(f"  span     : {opens} to {closes}")
    print(f"  quarters : {len(dl.quarters_between(opens, closes))}")
    print(f"  forms    : delisting {', '.join(dl.DELISTING_FORMS)};")
    print(f"             deregistration {', '.join(dl.DEREGISTRATION_FORMS)}")
    print( "             A Form 15 is NOT a delisting and is never summed with")
    print( "             the 25s: it can be filed by a company that was never")
    print( "             listed, and counting it would make the survivorship")
    print( "             bound look tighter than it is.")
    print()
    try:
        register = dl.build(opens, closes)
    except (dl.TraceCorpusRefused, ResponseNotTheDocument) as exc:
        print("REFUSED, and nothing was written:")
        print()
        print(exc)
        return 4
    out = dl.write_register(register)
    print(f"wrote {out}")
    print()
    print("Counts, and they are counts rather than estimates")
    for form, n in sorted(register.by_form().items()):
        kind = "DELISTING" if form in dl.DELISTING_FORMS else "deregistration"
        print(f"  {n:>6}  {form:<10} {kind}")
    print(f"  {len(register.delistings):>6}  delisting filings in total")
    print(f"  {register.distinct_delisted_ciks():>6}  DISTINCT delisted issuers"
          " -- the missing set's denominator")
    print()
    print("Coverage fraction: NOT SCORED. It is N/(N+M) and there is no N:")
    print("no archive exists, so the number of names covered is unknown.")
    print("Refusing rather than assuming one, because a fraction computed")
    print("against an assumed archive is the defect this register exists to")
    print("prevent, wearing the register's own clothes.")
    return 0


def cmd_sweep(args) -> int:
    try:
        reg = Registration.load(args.registration)
    except FileNotFoundError:
        print(f"{args.registration} not found. Run `init` first.")
        return 1

    try:
        reg.require_complete()
    except RegistrationIncomplete as exc:
        print(exc)
        return 2

    # P114: a sweep may not read a corpus git cannot produce again. This runs
    # BEFORE the master is loaded and before a document is opened, because a
    # refusal that has already done the work it was refusing is not a refusal.
    loose = uncommitted_routes([c.retrieval_route for c in reg.corpora])
    if loose:
        for route, detail in loose:
            print(summaries.render(
                "corpus_not_committed",
                f"corpus:{route}",
                {"route": route, "detail": detail},
            ).summary)
        print()
        print("Nothing swept. Commit the corpus and re-run: a proposal raised")
        print("over material no commit carries cannot be replayed from the")
        print("parameter hash it would carry, and rule 1 requires that it can.")
        return 6

    master, problems = _load_master(reg)
    for prob in problems:
        print(f"master: {prob}")
    if not master.per_market:
        print()
        print("No security master loaded, so the entity fence has no binding")
        print("layer and every machine-origin proposal would refuse to score.")
        print("Nothing swept.")
        return 5
    unreadable = master.unreadable_markets(reg.master_coverage_floor)
    # A market with no master at all is unreadable for the same reason as one
    # below the floor, and is named the same way.
    for c in reg.corpora:
        code = (resolve(c.market).code if resolve(c.market) else c.market)
        if code not in master.per_market and c.market not in master.per_market:
            unreadable.setdefault(c.market, "no security master loaded for this market")

    # A corpus whose market the master does not cover is refused here rather
    # than swept and silently under-fenced.
    corpora: List[SweepCorpus] = []
    for c in reg.corpora:
        if c.market in unreadable:
            print(f"skipping corpus {c.corpus_id!r}: {unreadable[c.market]}")
            continue
        # One copy of the skip rule, in corpusio, covering the route itself as
        # well as the files inside it. This loop had the second and not the
        # first, so a route pointed at an underscore directory was read whole.
        docs = corpus_documents(c.retrieval_route)
        if not docs and not args.transcript:
            print(f"skipping corpus {c.corpus_id!r}: no documents at {c.retrieval_route}")
            continue
        corpora.append(
            SweepCorpus(c.corpus_id, Partition(c.partition), docs or ["(transcript)"])
        )
    if not corpora:
        print("no readable corpus. Nothing swept.")
        return 3

    if not args.transcript and not reg.agent_model:
        print(
            "agent_model is not registered (§13 row 39). Refusing rather than "
            "defaulting: a sweep whose clerk is unrecorded cannot be compared "
            "with the next one. Nothing swept."
        )
        return 7

    try:
        client = (
            TranscriptClient(args.transcript)
            if args.transcript
            else AnthropicClient(
                model=reg.agent_model,
                # §13 row 40, read from the registration and from nowhere else.
                strict=reg.structured_outputs_strict,
            )
        )
    except ClientRefusal as exc:
        print(exc)
        return 4

    exclusivity = {c.event_class: None for c in reg.discoverable_classes}
    corpus_modes = {
        c.corpus_id: ScoringMode(c.scoring_mode or reg.default_scoring_mode)
        for c in reg.corpora
    }
    grid = [
        GridCell(c.event_class, "declared discoverable population",
                 f"a mechanism drawn from the {c.event_class} cell")
        for c in reg.discoverable_classes
    ]

    ledger = Ledger(args.ledger, parameter_hash=reg.hash())
    config = ScanConfig(
        parameter_hash=reg.hash(),
        # §7.2's audit fraction comes from the registration and from nowhere
        # else: it was a default in two places and registered in neither until
        # 27 August 2026.
        audit_fraction=reg.audit_fraction,
        default_scoring_mode=ScoringMode(reg.default_scoring_mode),
        exclusivity=exclusivity,
        corpus_modes=corpus_modes,
        entity_fence=master.as_fence(
            lexicon=frozenset(reg.lexicon),
            stopwords=frozenset(reg.rulebook_stopwords),
        ),
        control_arm_ratio=reg.control_arm_ratio,
        control_arm_seed=reg.control_arm_seed,
        policy=SegmentPolicy(
            theta=reg.theta,
            delta_min_floor=reg.delta_min_floor,
            segment_sessions=args.segment_sessions,
            calibration_reserve_sessions=args.calibration_reserve,
        ),
        span_start=date.fromisoformat(args.span_start),
    )

    print(f"registration {reg.hash()} stamped {reg.registered_at}")
    if any((c.scoring_mode or reg.default_scoring_mode) == "pre_archive"
           for c in reg.corpora):
        print(
            f"archive opens {reg.archive_opens}; pre_archive corpora must "
            "contain only material predating it. Document dates are NOT "
            "checked: that guarantee rests on your curation of the folder."
        )
    print(master.render(floor=reg.master_coverage_floor))
    print()

    # A transcript replay costs nothing and has no usage to read, so the guard
    # is not installed rather than being installed and told to report zero.
    guard = None if args.transcript else _cost_guard(client, args.cost_ceiling_usd)
    try:
        result = scan(client, corpora, grid, config, ledger, after_corpus=guard)
    except CostCeilingExceeded as exc:
        print()
        print(exc)
        print()
        print("STOPPED, and not truncated. The corpora already swept produced")
        print("proposals that were NOT registered: the abort happens inside the")
        print("gather loop, before the control arm is drawn and before a single")
        print("record reaches the ledger, so what exists is a measurement of")
        print("what a sweep costs and no partial sweep at all. A partial book")
        print("presented as a book is the defect this refuses.")
        ledger.close()
        return 8
    print(result.render(ledger))
    print()
    if not args.transcript:
        # **The figure the operator is owed, measured and not projected.** The
        # guard's projection answers *may this continue*; this answers *what
        # did it cost*, and the two are different questions. A run that printed
        # only the projection would leave the only number anyone can check
        # afterwards being an estimate made before most of the calls happened.
        print(client.spend().render("TOTAL for this sweep"))
        print()
    print(f"ledger: {args.ledger}")
    if result.blocked_on_operator:
        print()
        print(f"{len(result.blocked_on_operator)} draft(s) awaiting your delta_min,")
        print("registered sign, ratified pre-mortem and literature search.")
        print("That queue is the layer's steady state, not a failure of it.")
    ledger.close()
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fntn.scanner",
        description=(
            "Agent discovery layer (spec §3.7). Locates class-level mechanisms "
            "and produces observation directives at zero capital. Produces no "
            "trading signal and cannot."
        ),
    )
    parser.add_argument("--registration", default=DEFAULT_REG)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="write a blank registration form")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_markets = sub.add_parser("markets", help="show market profiles and constructions")
    p_markets.set_defaults(func=cmd_markets)

    p_tmpl = sub.add_parser("template", help="write a registration prefilled for all markets")
    p_tmpl.add_argument("--force", action="store_true")
    p_tmpl.set_defaults(func=cmd_template)

    p_check = sub.add_parser("check", help="report what is still missing")
    p_check.set_defaults(func=cmd_check)

    p_trace = sub.add_parser(
        "trace", help="run the §9.4 trace harness; measures machinery, not market"
    )
    p_trace.add_argument("--labelled", default="docs/labelled_proposals.json")
    p_trace.set_defaults(func=cmd_trace)

    p_rd = sub.add_parser(
        "ratify-draw",
        help="write the operator ratification worksheet (§13 rows 21a, 21b)",
    )
    p_rd.add_argument("--labelled", default="docs/labelled_proposals.json")
    p_rd.add_argument("--out", help="default docs/ratification_draw_<date>.md")
    p_rd.add_argument("--on", help="date to stamp the file with, ISO")
    p_rd.add_argument("--overwrite", action="store_true")
    p_rd.set_defaults(func=cmd_ratify_draw)

    p_rr = sub.add_parser(
        "ratify-reveal",
        help="reveal the clerk labels and report agreement as a count",
    )
    p_rr.add_argument("labels", help="JSON: {subject_id: class_level|not_class_level}")
    p_rr.add_argument("--labelled", default="docs/labelled_proposals.json")
    p_rr.set_defaults(func=cmd_ratify_reveal)

    p_rep = sub.add_parser(
        "report", help="write the run report from the ledger (§9.2)"
    )
    p_rep.add_argument("--ledger", default="fntn_discovery.db")
    p_rep.add_argument("--dir", default="docs/runs")
    p_rep.add_argument("--out", help="explicit path, bypassing the dated name")
    p_rep.add_argument("--on", help="date to stamp the report with, ISO")
    p_rep.add_argument("--budget-abandoned", type=int, default=None,
                       help="override the ledger's count; normally read from it")
    p_rep.add_argument("--open-items", default="docs/OPEN_ITEMS.md",
                       help="the register the binding path is read out of")
    p_rep.set_defaults(func=cmd_report)

    p_tf = sub.add_parser(
        "trace-filings",
        help="fetch one block of Form 4 filings into the fenced §9.4 corpus",
    )
    p_tf.add_argument("--on", help="index date, ISO. Defaults to today")
    p_tf.add_argument("--limit", type=int, default=None,
                      help="override the block size; normally left alone")
    p_tf.set_defaults(func=cmd_trace_filings)

    p_dl = sub.add_parser(
        "delisting-register",
        help="build the Form 25 / 25-NSE / 15 delisting register from EDGAR",
    )
    p_dl.add_argument("--opens", default=None,
                      help="span start, ISO. Defaults to the registration's "
                           "archive_opens, because the span the register must "
                           "cover is the archive's and not one chosen here")
    p_dl.add_argument("--closes", default=None, help="span end, ISO. Defaults to today")
    p_dl.set_defaults(func=cmd_delisting_register)

    p_sweep = sub.add_parser("sweep", help="run a sweep, if registration is complete")
    p_sweep.add_argument("--transcript", help="replay a saved payload instead of calling the model")
    # There is deliberately no --model. The pin is a registered field (§13 row
    # 39) and a CLI override would let a sweep run under a model the parameter
    # hash does not name, which is the ledger recording the wrong clerk.
    p_sweep.add_argument(
        "--cost-ceiling-usd", type=float, default=4.0,
        help=(
            "stop after the first corpus if the projected cost of the whole "
            "sweep exceeds this. Default 4.0 against a 5.00 balance. Set to 0 "
            "to disable the guard, which is a decision and not a default"
        ),
    )
    p_sweep.add_argument("--ledger", default="fntn_discovery.db")
    p_sweep.add_argument("--segment-sessions", type=int, default=0,
                         help="design-segment sessions. 0 until the archive exists")
    p_sweep.add_argument("--calibration-reserve", type=int, default=0)
    p_sweep.add_argument("--span-start", default="2024-01-01")
    p_sweep.set_defaults(func=cmd_sweep)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
