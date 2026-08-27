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

import subprocess
from pathlib import Path, PurePosixPath
from typing import List, Sequence, Tuple

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


def uncommitted_routes(routes: Sequence[str]) -> List[Tuple[str, str]]:
    """Corpus routes git cannot produce again, each with the reason.

    **The invariant this exists for, and it is aimed at a CLASS rather than an
    instance.** Three times this project has depended on material that was not
    retrievable: the raw fetched pages were never retained, the object behind
    the chain's first hash survives only as a reconstruction, and the corpus the
    twelve queued drafts were swept from is in no commit at all. **Each was
    closed as an instance and the class stayed open**, which is how it recurred
    twice more. The class is *material that decided something was not committed
    at the moment it decided it*, and the only closure that addresses the class
    is a refusal: **a sweep may not read a corpus git cannot produce again.**

    Returns ``[]`` when every route is clean and committed, which is the
    permissive answer and is therefore the one that must be earned. Anything
    else is a list of ``(route, reason)``, **and the reason names WHICH of three
    very different states obtains**, because "not committed" spans an untracked
    directory, a modified file and a tree that is not a repository at all, and a
    reader must not have to guess which.

    *The cost, stated.* A corpus fetched and swept in one sitting must now be
    committed between the two, which is one extra step in every session that
    ever adds material. **That is the price of being able to say afterwards what
    was read**, and the sessions that discovered they could not say it paid more.
    """

    problems: List[Tuple[str, str]] = []
    for route in routes:
        path = Path(route)
        if not path.exists():
            problems.append((route, "the route does not exist on disk"))
            continue
        inside = _git("rev-parse", "--is-inside-work-tree", cwd=path)
        if inside != "true":
            problems.append(
                (route, "not a git work tree, so nothing here can be retrieved "
                        "again by commit")
            )
            continue
        # --untracked-files=all so an untracked FILE inside a tracked directory
        # is reported, not merely an untracked directory. A corpus one file
        # larger than its last commit is exactly the silent case.
        status = _git("status", "--porcelain", "--untracked-files=all", "--",
                      str(path), cwd=path)
        if status:
            names = [line[3:] for line in status.splitlines()[:4]]
            kind = "untracked" if any(
                line.startswith("??") for line in status.splitlines()
            ) else "modified"
            problems.append(
                (route, f"{kind} content that no commit carries: "
                        + ", ".join(names)
                        + ("" if len(status.splitlines()) <= 4 else ", and more"))
            )
    return problems


def _git(*args: str, cwd: Path) -> str:
    """Git, or the empty string. Never raises, and never guesses.

    An empty result is not read as success anywhere above: every caller tests
    for the value it needs, so a git that is absent produces a refusal rather
    than a pass.
    """

    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd if cwd.is_dir() else cwd.parent),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        return ""
