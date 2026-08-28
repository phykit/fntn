"""Drive the intake path over the run of record's own emissions, before and after."""
import json, tempfile, os
from collections import Counter
from datetime import datetime, timezone
from fntn.scanner.clients import TranscriptClient
from fntn.scanner.discovery import Corpus, GridCell
from fntn.scanner.records import Partition, ScoringMode
from fntn.scanner.ledger import Ledger
from fntn.scanner.run import scan, ScanConfig
from fntn.scanner.params import Registration
from fntn.scanner.cli import _load_master

reg = Registration.load("discovery_registration.json")
master, problems = _load_master(reg)
print("master problems:", problems or "none")
NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)

def run(label, classes):
    fd, path = tempfile.mkstemp(suffix=".db"); os.close(fd); os.unlink(path)
    ledger = Ledger(path, parameter_hash=reg.hash())
    client = TranscriptClient("docs/replay/run_of_record_agent_emissions.json")
    corpora = [Corpus("buyback", Partition.EXTERNAL, ["(transcript)"]),
               Corpus("earnings_event", Partition.EXTERNAL, ["(transcript)"])]
    grid = [GridCell(c, "declared discoverable population",
                     f"a mechanism drawn from the {c} cell") for c in classes]
    cfg = ScanConfig(
        parameter_hash=reg.hash(),
        audit_fraction=reg.audit_fraction,
        exclusivity={c: None for c in classes},
        corpus_modes={"buyback": ScoringMode.CROSS_MARKET,
                      "earnings_event": ScoringMode.CROSS_MARKET},
        entity_fence=master.as_fence(lexicon=frozenset(reg.lexicon),
                                     stopwords=frozenset(reg.rulebook_stopwords)),
        control_arm_ratio=reg.control_arm_ratio,
        control_arm_seed=reg.control_arm_seed,
    )
    res = scan(client, corpora, grid, cfg, ledger, now=NOW)
    codes = Counter(dict(ledger.code_distribution()))
    print(f"\n=== {label} ===")
    print(f"  discoverable classes : {len(classes)}")
    print(f"  counts               : {ledger.counts()}")
    print(f"  refusal codes        : {dict(sorted(codes.items()))}")
    ledger.close(); os.path.exists(path) and os.unlink(path)
    return codes

before = run("B. Repaired code, the THREE classes of the run of record",
             ["buyback", "earnings_event", "major_holdings_change"])
after = run("C. Repaired code, all SEVEN classes (the 28 Aug row 22 decision)",
            sorted(c.event_class for c in reg.discoverable_classes))
print()
print("what moved:")
for code in sorted(set(before) | set(after)):
    b, a = before.get(code, 0), after.get(code, 0)
    if b != a:
        print(f"  {code:38s} {b:3d} -> {a:3d}")
