"""Column A: the SAME fixture against the PRE-REPAIR tree at db1c463.

Run from an extracted db1c463 tree, not from this one -- the point is to
exercise the old code. See docs/REPLAY_2026-08-28.md for the recipe.

NON-EVIDENTIARY. It drives the intake path over a recording and measures
nothing about any market.
"""

import os, tempfile
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
NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)
classes = sorted(c.event_class for c in reg.discoverable_classes)
fd, path = tempfile.mkstemp(suffix=".db"); os.close(fd); os.unlink(path)
ledger = Ledger(path, parameter_hash=reg.hash())
client = TranscriptClient("run_of_record_agent_emissions.json")
corpora = [Corpus("buyback", Partition.EXTERNAL, ["(transcript)"]),
           Corpus("earnings_event", Partition.EXTERNAL, ["(transcript)"])]
grid = [GridCell(c, "declared discoverable population", f"drawn from {c}") for c in classes]
cfg = ScanConfig(parameter_hash=reg.hash(), audit_fraction=reg.audit_fraction,
                 exclusivity={c: None for c in classes},
                 corpus_modes={"buyback": ScoringMode.CROSS_MARKET,
                               "earnings_event": ScoringMode.CROSS_MARKET},
                 entity_fence=master.as_fence(lexicon=frozenset(reg.lexicon),
                                              stopwords=frozenset(reg.rulebook_stopwords)),
                 control_arm_ratio=reg.control_arm_ratio,
                 control_arm_seed=reg.control_arm_seed)
scan(client, corpora, grid, cfg, ledger, now=NOW)
print("  discoverable classes :", len(classes))
print("  counts               :", ledger.counts())
print("  refusal codes        :", dict(sorted(dict(ledger.code_distribution()).items())))
