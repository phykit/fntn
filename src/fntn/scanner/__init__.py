"""From Narrative to Null -- agent discovery scanner.

Spec: v1.14 (proposed), §3.7.  Procedure at the intake surface; the discovery
agent itself is apparatus and takes an Annex A.1 row.

What this package does: uses agents to locate candidate *mechanisms*, turns each
into a §3.6.2 pointer-tier intake record under a fail-fast ingestion discipline,
screens it, maps it to a stream, and produces an observation directive that runs
at zero capital once the operator supplies the two things only they may supply.

What this package cannot do, structurally: emit a trading signal, size a
position, amend a family, supply a parameter, create a grammar row, or enter the
item pipeline.  A pointer's only reachable output is a directive, and that has
not changed because the pointer was raised by a machine.
"""

from .codes import ALL_CODES, INTAKE_ORDER, OBSERVATION_ORDER, coverage
from .fences import (
    ImportFenceBreach,
    QueryFence,
    QueryFenceBreach,
    QueryKind,
    assert_import_fence,
)
from .ingest import Mode, intake_runner, observation_runner
from .ledger import Ledger
from .records import (
    Directive,
    EvidenceTier,
    IntakeRecord,
    Item,
    Origin,
    Partition,
    PreMortem,
    Proposal,
    Provenance,
    ScoringMode,
    SegmentSpan,
    StreamStatus,
    Verdict,
)
from .segment import ReuseLedger, SegmentPolicy
from .run import ScanConfig, ScanResult, scan

__version__ = "1.13.0"

__all__ = [
    "ALL_CODES",
    "INTAKE_ORDER",
    "OBSERVATION_ORDER",
    "coverage",
    "QueryFence",
    "QueryFenceBreach",
    "QueryKind",
    "ImportFenceBreach",
    "assert_import_fence",
    "Mode",
    "intake_runner",
    "observation_runner",
    "Ledger",
    "Directive",
    "EvidenceTier",
    "IntakeRecord",
    "Item",
    "Origin",
    "Partition",
    "PreMortem",
    "Proposal",
    "Provenance",
    "ScoringMode",
    "SegmentSpan",
    "StreamStatus",
    "Verdict",
    "ReuseLedger",
    "SegmentPolicy",
    "ScanConfig",
    "ScanResult",
    "scan",
]
