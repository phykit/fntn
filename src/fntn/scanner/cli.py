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
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from .clients import AnthropicClient, ClientRefusal, TranscriptClient
from .discovery import Corpus as SweepCorpus, GridCell
from .fences import QueryFence
from .ledger import Ledger
from .markets import MARKETS, render as render_markets, resolve
from .master import SecurityMaster
from .params import Registration, RegistrationIncomplete
from .records import Partition, ScoringMode, SegmentSpan
from .run import ScanConfig, scan
from .segment import SegmentPolicy
from .trace import TraceHarness, load_labelled

DEFAULT_REG = "discovery_registration.json"


def _load_master(reg: Registration) -> tuple:
    """Load every master file. Returns (master, problems).

    A missing or unreadable file is a refusal with the file named, not a
    traceback: the template prefills a path per market and most of them will
    not exist yet, which is an ordinary state rather than an error.
    """

    master = SecurityMaster()
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
        entity_fence=master.as_fence(stopwords=frozenset(reg.rulebook_stopwords)),
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
        docs = []
        route = Path(c.retrieval_route)
        for path in sorted(route.glob("*")) if route.is_dir() else []:
            # Underscore-prefixed files are corpus bookkeeping, not corpus. The
            # manifest records what was fetched; feeding it to the agent as
            # material would put source URLs and filenames in front of it.
            if path.name.startswith("_") or not path.is_file():
                continue
            docs.append(path.read_text(encoding="utf-8", errors="replace")[:20000])
        if not docs and not args.transcript:
            print(f"skipping corpus {c.corpus_id!r}: no documents at {c.retrieval_route}")
            continue
        corpora.append(
            SweepCorpus(c.corpus_id, Partition(c.partition), docs or ["(transcript)"])
        )
    if not corpora:
        print("no readable corpus. Nothing swept.")
        return 3

    try:
        client = (
            TranscriptClient(args.transcript)
            if args.transcript
            else AnthropicClient(model=args.model)
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
        default_scoring_mode=ScoringMode(reg.default_scoring_mode),
        exclusivity=exclusivity,
        corpus_modes=corpus_modes,
        entity_fence=master.as_fence(
            stopwords=frozenset(reg.rulebook_stopwords)
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
    result = scan(client, corpora, grid, config, ledger)
    print(result.render(ledger))
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

    p_sweep = sub.add_parser("sweep", help="run a sweep, if registration is complete")
    p_sweep.add_argument("--transcript", help="replay a saved payload instead of calling the model")
    p_sweep.add_argument("--model", default="claude-opus-4-6")
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
