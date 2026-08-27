"""Reading a corpus directory, in one place, so the skip rule has one copy.

**Why this is a module and not four lines inside `cmd_sweep`.** The rule that
underscore-prefixed names are bookkeeping and not corpus was written once, in
the sweep's own loop, and it applied to *files inside a route* and to nothing
else. A route pointed **at** an underscore directory therefore had its contents
read in full, which is the failure `corpora/_trace_filings` would have turned
from a bookkeeping leak into an entity-fence breach: those filings name issuers
and dates, and the corpus is what the agent is shown.

**This module is deliberately not imported by `discovery.py`.** It reads paths;
the agent reads documents it is handed. `test_discovery_reaches_no_module_that_
names_the_trace_corpus` walks the import closure and asserts it.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import List

#: Read at most this many characters per document, as the sweep always has.
DOCUMENT_CHARS = 20000


def is_fenced_path(route: str | Path) -> bool:
    """Whether any component of ``route`` is underscore-prefixed.

    Any component and not merely the last, because `_trace_filings/2026`
    reaches the same material one level down.
    """

    return any(
        part.startswith("_")
        for part in PurePosixPath(str(route).strip()).parts
    )


def corpus_documents(route: str | Path) -> List[str]:
    """Every readable document at ``route``, or nothing if the route is fenced.

    **Returns an empty list rather than raising**, because the caller's job is
    to report a corpus as unreadable and carry on, and a fenced route is
    unreadable in exactly the sense that matters: there is nothing there the
    agent may be shown. `Corpus.__post_init__` is what refuses outright, so a
    fenced route should never reach here at all; this is the second lock.
    """

    path = Path(route)
    if is_fenced_path(route) or not path.is_dir():
        return []
    docs: List[str] = []
    for item in sorted(path.glob("*")):
        # Underscore-prefixed files are corpus bookkeeping, not corpus. The
        # manifest records what was fetched; feeding it to the agent as
        # material would put source URLs and filenames in front of it.
        if item.name.startswith("_") or not item.is_file():
            continue
        docs.append(item.read_text(encoding="utf-8", errors="replace")[:DOCUMENT_CHARS])
    return docs
