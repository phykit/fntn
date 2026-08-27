"""The SQLite decision ledger for the scanner.

Keyed on parameter hash and subject, per §9.2.  Five tables and one rule that
governs all of them: **nothing is deleted and nothing is overwritten.**  A
proposal abandoned at the first ingestion point stays in the ledger with its
reason code and its rendered summary, because an abort that writes nothing
shrinks §7.1's denominator silently and a funnel whose product is legible
refusal cannot lose the refusals.

``rejection_summary`` is stored in a column no query in this module joins on.
That is deliberate and structural: the summary is display-only, so a badly
written one can mislead a reader and cannot mislead the system.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .records import Directive, Proposal, Refusal

SCHEMA = """
CREATE TABLE IF NOT EXISTS proposal (
    subject_id      TEXT PRIMARY KEY,
    parameter_hash  TEXT NOT NULL,
    origin          TEXT NOT NULL,
    event_class     TEXT NOT NULL,
    measured_on     TEXT NOT NULL,
    event_definition TEXT NOT NULL,
    source_ref      TEXT NOT NULL,
    source_partition TEXT NOT NULL,
    drawn_from_grid_cell TEXT,
    raised_at       TEXT NOT NULL,
    outcome         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS refusal (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id      TEXT NOT NULL,
    parameter_hash  TEXT NOT NULL,
    code            TEXT NOT NULL,
    surface         TEXT NOT NULL,
    fields_json     TEXT NOT NULL,
    author          TEXT NOT NULL,
    at              TEXT NOT NULL,
    rejection_summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS directive (
    directive_id    TEXT PRIMARY KEY,
    subject_id      TEXT NOT NULL,
    parameter_hash  TEXT NOT NULL,
    origin          TEXT NOT NULL,
    event_class     TEXT NOT NULL,
    measured_on     TEXT NOT NULL,
    stream          TEXT NOT NULL,
    stream_status   TEXT NOT NULL,
    scoring_mode    TEXT NOT NULL,
    span_start      TEXT NOT NULL,
    span_end        TEXT NOT NULL,
    span_population TEXT NOT NULL,
    span_sessions   INTEGER NOT NULL,
    n_min           INTEGER NOT NULL,
    delta_min       REAL,
    registered_sign INTEGER,
    registered_at   TEXT,
    state           TEXT NOT NULL,
    verdict         TEXT
);

CREATE TABLE IF NOT EXISTS declined_feed (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id      TEXT NOT NULL,
    feed            TEXT NOT NULL,
    reason_code     TEXT NOT NULL,
    at              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS query_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    at              TEXT NOT NULL,
    kind            TEXT NOT NULL,
    population_key  TEXT NOT NULL,
    actor           TEXT NOT NULL,
    text            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS budget_decision (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id      TEXT NOT NULL,
    parameter_hash  TEXT NOT NULL,
    point           TEXT NOT NULL,
    elapsed_s       REAL NOT NULL,
    budget_s        REAL NOT NULL,
    attempts        INTEGER NOT NULL,
    exhausted       INTEGER NOT NULL,
    at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS refusal_code_idx ON refusal(code);
CREATE INDEX IF NOT EXISTS refusal_subject_idx ON refusal(subject_id);
"""


class Ledger:
    def __init__(self, path: str | Path = ":memory:", parameter_hash: str = "unfrozen"):
        self.parameter_hash = parameter_hash
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        with closing(self.conn.cursor()) as cur:
            cur.executescript(SCHEMA)
        self.conn.commit()

    # -- writes ------------------------------------------------------------

    def write_proposal(self, subject_id: str, p: Proposal, outcome: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO proposal VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                subject_id,
                self.parameter_hash,
                p.origin.value,
                p.event_class,
                p.measured_on_intention,
                p.event_definition,
                p.source_ref,
                p.source_partition.value,
                p.drawn_from_grid_cell,
                (p.raised_at or datetime.now(timezone.utc)).isoformat(),
                outcome,
            ),
        )
        self.conn.commit()

    def write_refusal(self, r: Refusal) -> None:
        self.conn.execute(
            "INSERT INTO refusal "
            "(subject_id,parameter_hash,code,surface,fields_json,author,at,"
            "rejection_summary) VALUES (?,?,?,?,?,?,?,?)",
            (
                r.subject_id,
                self.parameter_hash,
                r.code,
                r.surface,
                json.dumps(r.fields, default=str, sort_keys=True),
                r.author,
                (r.at or datetime.now(timezone.utc)).isoformat(),
                r.summary,
            ),
        )
        self.conn.commit()

    def write_refusals(self, refusals: Iterable[Refusal]) -> None:
        for r in refusals:
            self.write_refusal(r)

    def write_directive(self, d: Directive, state: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO directive VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                d.directive_id,
                d.intake_id,
                self.parameter_hash,
                d.origin.value,
                d.event_class,
                d.measured_on,
                d.stream,
                d.stream_status.value,
                d.scoring_mode.value,
                d.span.start.isoformat(),
                d.span.end.isoformat(),
                d.span.population_key,
                d.span.sessions,
                d.n_min,
                d.delta_min,
                d.registered_sign,
                d.registered_at.isoformat() if d.registered_at else None,
                state,
                d.verdict.value if d.verdict else None,
            ),
        )
        self.conn.commit()

    def write_budget_decisions(self, decisions: Iterable) -> None:
        """The elapsed time, the budget in force, and the decision.

        **This is what a replay reads instead of a clock.** The decision was
        taken once, when the work ran; storing only the refusal would leave a
        replay with nothing to read and a fresh clock to consult, and the run's
        refusal set would then depend on the machine that replayed it.
        """

        rows = [
            (
                d.subject_id, self.parameter_hash, d.point, d.elapsed_s,
                d.budget_s, d.attempts, int(d.exhausted), d.at,
            )
            for d in decisions
        ]
        if not rows:
            return
        self.conn.executemany(
            "INSERT INTO budget_decision "
            "(subject_id,parameter_hash,point,elapsed_s,budget_s,attempts,"
            "exhausted,at) VALUES (?,?,?,?,?,?,?,?)",
            rows,
        )
        self.conn.commit()

    def budget_decisions(self, subject_id: str | None = None) -> List[Dict]:
        sql = ("SELECT subject_id, point, elapsed_s, budget_s, attempts, "
               "exhausted, at FROM budget_decision")
        args: tuple = ()
        if subject_id is not None:
            sql += " WHERE subject_id = ?"
            args = (subject_id,)
        sql += " ORDER BY id"
        return [
            {
                "subject_id": r["subject_id"], "point": r["point"],
                "elapsed_s": r["elapsed_s"], "budget_s": r["budget_s"],
                "attempts": r["attempts"], "exhausted": bool(r["exhausted"]),
                "at": r["at"],
            }
            for r in self.conn.execute(sql, args)
        ]

    def budget_abandoned(self) -> int:
        """Subjects abandoned to the ceiling. Printed in every report, at zero too."""

        return int(
            self.conn.execute(
                "SELECT COUNT(DISTINCT subject_id) FROM budget_decision "
                "WHERE exhausted = 1"
            ).fetchone()[0]
        )

    def write_declined_feed(self, subject_id: str, feed: str, code: str) -> None:
        self.conn.execute(
            "INSERT INTO declined_feed (subject_id,feed,reason_code,at) VALUES (?,?,?,?)",
            (subject_id, feed, code, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def write_query_log(self, entries: Iterable) -> None:
        for e in entries:
            self.conn.execute(
                "INSERT INTO query_log (at,kind,population_key,actor,text) "
                "VALUES (?,?,?,?,?)",
                (e.at.isoformat(), e.kind.value, e.population_key, e.actor, e.text),
            )
        self.conn.commit()

    # -- reads -------------------------------------------------------------

    def emitted_codes(self) -> List[str]:
        return [r["code"] for r in self.conn.execute("SELECT DISTINCT code FROM refusal")]

    def code_distribution(self) -> List[Tuple[str, int]]:
        rows = self.conn.execute(
            "SELECT code, COUNT(*) n FROM refusal GROUP BY code ORDER BY n DESC, code"
        )
        return [(r["code"], r["n"]) for r in rows]

    def counts(self) -> Dict[str, int]:
        def one(sql: str) -> int:
            return int(self.conn.execute(sql).fetchone()[0])

        return {
            "proposals": one("SELECT COUNT(*) FROM proposal"),
            "refusals": one("SELECT COUNT(*) FROM refusal"),
            "directives": one("SELECT COUNT(*) FROM directive"),
            "registered": one(
                "SELECT COUNT(*) FROM directive WHERE registered_at IS NOT NULL"
            ),
            "promoted": one(
                "SELECT COUNT(*) FROM directive WHERE verdict = 'promoted'"
            ),
            "declined_feeds": one("SELECT COUNT(*) FROM declined_feed"),
            "queries": one("SELECT COUNT(*) FROM query_log"),
        }

    def declined_feed_distribution(self) -> List[Tuple[str, int]]:
        """The §3.6.5 log, reported at freeze beside the roster decision.

        If the ideas raised persistently point at streams the roster lacks, that
        is evidence the roster is mismatched to the hypothesis space, and the
        freeze is where rosters change.  It is not evidence for bypassing §0.6.
        """

        rows = self.conn.execute(
            "SELECT feed, COUNT(*) n FROM declined_feed GROUP BY feed ORDER BY n DESC, feed"
        )
        return [(r["feed"], r["n"]) for r in rows]

    def summaries_for(self, subject_id: str) -> List[str]:
        rows = self.conn.execute(
            "SELECT rejection_summary FROM refusal WHERE subject_id = ? ORDER BY id",
            (subject_id,),
        )
        return [r["rejection_summary"] for r in rows]

    def close(self) -> None:
        self.conn.close()
