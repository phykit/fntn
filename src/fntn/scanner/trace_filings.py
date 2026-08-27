"""The §9.4 trace corpus: SEC Form 4 filings, fetched and verified.

**What this is for.** §14's trace precondition requires §9.4's harness run to
its stopping rule *"including a minimum sample of the primary catalyst family's
live filing flow"*. The primary catalyst family is insider dealing, so the flow
is Form 4. `corpora/us` is rule text and exercises the machinery; only the
family's own flow exercises the family.

**What this is NOT for, and the containment is the point.** A Form 4 names an
issuer, a reporting owner and a transaction date. **That is precisely the
material the entity fence exists to keep out of a proposal.** This corpus is
therefore fenced three ways and none of them is a convention:

1. It lives at ``corpora/_trace_filings/``, underscore-prefixed, and
   ``Corpus.__post_init__`` **refuses to construct** a registration row whose
   ``retrieval_route`` has an underscore-prefixed component. A registration
   file naming it will not load.
2. ``corpusio.corpus_documents`` returns nothing for a fenced route, so the
   sweep's loader cannot read it even if one were somehow constructed.
3. **This module is not in ``discovery.py``'s import closure**, and a test
   walks that closure and asserts no module in it so much as names the path.

**Everything produced from it is stamped ``TRACE-NON-EVIDENTIARY``** and
inherits ``trace.py``'s refusal to register or admit a directive.

**The clerk is not involved.** Form 4 is a field-delimited regulatory form, so
per CLAUDE.md's first rule *even the clerk is replaced by a parser*: nothing
here calls a model.
"""

from __future__ import annotations

import hashlib
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .trace import NON_EVIDENTIARY

#: Where the corpus lives. Underscore-prefixed, and every fence above keys on
#: that prefix rather than on this constant, so moving it cannot unfence it.
CORPUS_ROOT = Path("corpora") / "_trace_filings"
RAW_ROOT = CORPUS_ROOT / "_raw"
MANIFEST = CORPUS_ROOT / "_manifest.tsv"
FETCH_LOG = RAW_ROOT / "_fetch.tsv"

#: **The sample size, chosen before fetching and justified from the rule that
#: consumes it.** §9.4's stopping rule reads: *"It runs in blocks; after each,
#: the marginal defect rate per hundred items is computed; when that falls
#: below a stated threshold for two consecutive blocks, tracing stops."*
#:
#: The rule's own unit is **one hundred items**, so a block is 100. That is the
#: smallest sample that yields a defect rate the rule can read without the
#: denominator being invented here, and it is chosen for that reason and not
#: because it is a round number.
#:
#: **Stated plainly, because it bears on binding-path step 4: one block cannot
#: discharge the stopping rule.** The rule requires the rate to fall below a
#: threshold *for two consecutive blocks*, so **two hundred items is the
#: arithmetic minimum** and the threshold itself is unstated in §9.4 and has no
#: §13 row. One block is what this phase fetches; what it buys is the first
#: block's rate, not a discharge.
BLOCK_SIZE = 100

#: **Not the main guard.** A previous session found sec.gov serving `curl` a
#: **698-byte stub** with a 200 status: the URL resolved and the document did
#: not arrive. A byte floor catches that particular stub and would not catch a
#: larger one, so the structural marker below is the guard and this is the
#: cheap first check. Set at 1,500 because the smallest plausible ownership
#: document carries a schema declaration, an issuer block, a reporting-owner
#: block and at least one transaction table, and the known stub is 698.
MIN_FORM4_BYTES = 1500
MIN_INDEX_BYTES = 4000

#: The structural markers. A response without its marker is **reported as the
#: failure it is** and never worked around.
FORM4_MARKER = "<ownershipDocument"
INDEX_MARKER = "Form Type"

# ---------------------------------------------------------------------------
# 8-K Item 2.02, the RE-POINTED step-4 family (§12.1 P126, P137)
# ---------------------------------------------------------------------------
#
# **Why this family and not Form 4 or Schedule 13D.** Step 4's primary catalyst
# family is `earnings_event` and its live filing flow is 8-K Item 2.02. The
# decisive reason is not the count of intake points it reaches: it is that
# **an 8-K's furnished press release is PROSE**, so it is the only candidate
# that exercises `extraction_schema_incomplete` against a model-mediated
# extraction path. Form 4 and Schedule 13D are field-delimited, and CLAUDE.md's
# first rule replaces the clerk with a parser wherever they are, so neither has
# a model anywhere near its extraction. **The path rule 1 is written against is
# the one this family is chosen to exercise.**
#
# **The route, and it is deterministic at every step.** The daily form index
# gives every 8-K filed on a day, with its accession path. **The index does NOT
# record which Items an 8-K carries**, so the item is read from the submission's
# own SGML header, which is field-delimited: a parser, not a clerk.
#
# ***PROVENANCE OF THE HEADER FORMAT: `named, unread`.*** Two spellings are
# accepted because both appear in EDGAR submissions, `ITEM INFORMATION:` in the
# human-readable header and `<ITEM>` in the machine header. **Neither has been
# read from a live response in this tree**, because `SEC_CONTACT` has never
# carried a usable identity. `item_codes` therefore REFUSES a submission
# carrying neither marker rather than concluding it is not an Item 2.02 filing:
# **absence of the field is not absence of the item**, and reading it as such
# would silently drop every filing whose header this parser does not understand.
EIGHTK_FORM = "8-K"
EIGHTK_ITEM = "2.02"

#: A submission text file carries the whole filing, header and exhibits. The
#: header alone runs to some hundreds of bytes and the furnished press release
#: is the bulk. Set at 2,000 on the same reasoning as `MIN_FORM4_BYTES`: it
#: catches the known 698-byte stub and nothing subtler, and the structural
#: marker below is the guard.
MIN_8K_BYTES = 2000

#: The structural marker for a submission text file. `verify_response` refuses
#: anything without it, so a login page, an error page or a stub cannot be
#: mistaken for a filing.
SUBMISSION_MARKER = "CONFORMED SUBMISSION TYPE"

#: The two spellings of the item field. Both are accepted; NEITHER present is a
#: refusal and never a negative answer.
ITEM_MARKERS = ("ITEM INFORMATION:", "<ITEM>")

SEC_HOST = "https://www.sec.gov"
DATA_HOST = "https://data.sec.gov"


class TraceCorpusRefused(RuntimeError):
    """Raised rather than defaulted. See each call site."""


class ResponseNotTheDocument(RuntimeError):
    """A response arrived and is not the document that was asked for.

    Separate from a transport error on purpose. A 200 carrying a stub is the
    failure mode that cost a previous session real time precisely because it
    looks like success, and calling it a network error would file it under the
    heading nobody re-reads.
    """


#: Characters that mark an unedited placeholder rather than a contact. The SEC
#: asks for a name and an email address; neither contains an angle bracket, and
#: `<name> <email>` is the exact string a documented example leaves behind.
_PLACEHOLDER_MARKERS = ("<", ">", "your.address@example.com", "example.com")


def user_agent() -> str:
    """The SEC fair-access identity, read from ``SEC_CONTACT``.

    **Refused rather than defaulted, and deliberately not substitutable.** The
    SEC's fair-access policy requires the caller to identify themselves. A
    placeholder would be a false statement made to a regulator's server in
    order to obtain data, which is not a configuration shortcut; and inventing
    a value would put an unverifiable string on every row of the manifest.

    ***AND UNTIL 27 August 2026 THIS FUNCTION DID NOT IMPLEMENT THE PARAGRAPH
    ABOVE.*** It tested `if not contact` and nothing else, so **an environment
    variable SET TO A PLACEHOLDER passed it.** The session that found this had
    `SEC_CONTACT` set to the literal string ``<name> <email>``, which the guard
    admitted and which would have gone to `sec.gov` in a `User-Agent` header on
    every request of a hundred-filing fetch. *The rule was written; the check
    tested presence and the rule is about content.*

    **Three refusals now, and the second and third are the new ones:**

    * **unset or blank** -- nothing to identify the caller with;
    * **placeholder markers** -- an angle bracket or a documented example
      address, which is an unedited template rather than a contact;
    * **no email address** -- the SEC asks for a name *and* an address, and a
      bare name gives their operators nothing to write to.

    *The shape checks are taken from the format the SEC itself publishes, not
    invented here. They cannot establish that a well-formed address is real,
    and they are not claimed to: what they establish is that nobody has left
    the example in place.*
    """

    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    if not contact:
        raise TraceCorpusRefused(
            "SEC_CONTACT is not set, so this fetch will not run.\n\n"
            "The SEC's fair-access policy requires the caller to identify "
            "themselves in the User-Agent. This module refuses to invent one "
            "and refuses to substitute a placeholder: a placeholder is a false "
            "statement made to a regulator's server to obtain data, and it "
            "would be recorded on every row of the manifest as though it were "
            "the contact.\n\n"
            "THE OPERATOR MUST SET IT. For example:\n"
            "    export SEC_CONTACT='Your Name your.address@example.com'\n\n"
            "Nothing is fetched and nothing is written until it is set."
        )

    lowered = contact.lower()
    hit = next((m for m in _PLACEHOLDER_MARKERS if m in lowered), None)
    if hit is not None:
        raise TraceCorpusRefused(
            f"SEC_CONTACT is set to what looks like an unedited placeholder: "
            f"{contact!r} contains {hit!r}.\n\n"
            "This fetch will not run. Sending a placeholder to sec.gov in a "
            "User-Agent is the false statement this module exists to refuse, "
            "and a variable that is SET is not thereby USABLE: until now this "
            "guard tested only that something was there.\n\n"
            "Set it to a real name and a real address you will answer:\n"
            "    export SEC_CONTACT='Ada Lovelace ada@her-own-domain.uk'\n\n"
            "Nothing is fetched and nothing is written until it is."
        )

    local, _, domain = contact.partition("@")
    if not local.strip() or not domain.strip() or "." not in domain:
        raise TraceCorpusRefused(
            f"SEC_CONTACT is set to {contact!r}, which carries no email "
            "address.\n\n"
            "The SEC's fair-access policy asks for a name AND an address, so "
            "that their operators can reach whoever is making the requests. A "
            "bare name identifies nobody they can write to, and this module "
            "will not send one and call it an identity.\n\n"
            "    export SEC_CONTACT='Ada Lovelace ada@her-own-domain.uk'\n\n"
            "Nothing is fetched and nothing is written until it is."
        )

    return f"fntn-trace-harness/1.0 ({contact})"


def verify_response(url: str, body: bytes, minimum: int, marker: str) -> str:
    """Assert the response IS the document, not merely that the URL resolved.

    Two checks and they are not redundant. The size catches the known stub; the
    marker catches everything shaped like a page and not like the document,
    which is the general case the stub is one instance of.
    """

    if len(body) < minimum:
        raise ResponseNotTheDocument(
            f"{url} returned {len(body)} bytes, below the {minimum}-byte floor. "
            f"A previous session recorded sec.gov serving a 698-byte stub with "
            f"a 200 status, which is this failure. It is reported rather than "
            f"worked around.\n\nFirst 200 bytes: {body[:200]!r}"
        )
    text = body.decode("utf-8", errors="replace")
    if marker not in text:
        raise ResponseNotTheDocument(
            f"{url} returned {len(body)} bytes with no {marker!r}. The size is "
            f"plausible and the content is not the document, which is why the "
            f"marker and not the size is the guard.\n\n"
            f"First 200 bytes: {body[:200]!r}"
        )
    return text


def fetch(url: str, minimum: int, marker: str, timeout: int = 30) -> Tuple[bytes, str]:
    """One GET, identified, verified. Returns (raw bytes, decoded text)."""

    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent(),
        "Accept-Encoding": "gzip, deflate",
        "Host": url.split("/")[2],
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise ResponseNotTheDocument(
            f"{url} returned HTTP {exc.code} {exc.reason}. Reported rather "
            f"than retried into a placeholder."
        ) from exc
    return body, verify_response(url, body, minimum, marker)


def daily_index_url(on: date) -> str:
    """EDGAR's daily form index: structured, not screen-scraped."""

    quarter = (on.month - 1) // 3 + 1
    return (
        f"{SEC_HOST}/Archives/edgar/daily-index/{on.year}/QTR{quarter}/"
        f"form.{on:%Y%m%d}.idx"
    )


def submissions_url(cik: str) -> str:
    """The submissions JSON for one filer: structured, not screen-scraped."""

    return f"{DATA_HOST}/submissions/CIK{int(cik):010d}.json"


def form4_rows(index_text: str) -> List[Tuple[str, str, str]]:
    """(CIK, company, path) for every Form 4 in a daily form index.

    A deterministic parser over a field-delimited file, per CLAUDE.md's first
    rule. The index is fixed-width with a dashed rule under the header; rows
    are split on runs of whitespace from the right, because a company name
    contains spaces and the three fields after it do not.
    """

    out: List[Tuple[str, str, str]] = []
    for line in index_text.splitlines():
        if not line.startswith("4 "):
            continue
        parts = line.rsplit(None, 3)
        if len(parts) != 4:
            continue
        company_field, cik, _filed, path = parts
        company = company_field[1:].strip()
        if not cik.isdigit():
            continue
        out.append((cik, company, path))
    return out


def eightk_rows(index_text: str) -> List[Tuple[str, str, str]]:
    """(CIK, company, path) for every 8-K in a daily form index.

    The same deterministic parser as `form4_rows` over the same fixed-width
    file. Split on runs of whitespace **from the right**, because a company
    name contains spaces and the three fields after it do not.

    Amendments are excluded: a line beginning `8-K/A ` does not match `8-K `
    plus a space, and an amendment restates a filing already ingested, which
    **nothing in the item pipeline's eleven points addresses**
    (`docs/PIPELINE_9_4_2026-08-27.md`). Including them would put an
    undetermined object in a measured denominator.
    """

    prefix = EIGHTK_FORM + " "
    out: List[Tuple[str, str, str]] = []
    for line in index_text.splitlines():
        if not line.startswith(prefix):
            continue
        parts = line.rsplit(None, 3)
        if len(parts) != 4:
            continue
        company_field, cik, _filed, path = parts
        company = company_field[len(EIGHTK_FORM):].strip()
        if not cik.isdigit():
            continue
        out.append((cik, company, path))
    return out


def item_codes(submission_text: str) -> List[str]:
    """The Item numbers an 8-K submission declares, from its own SGML header.

    **A parser over a field-delimited header, never a model.** Two spellings
    are accepted, `ITEM INFORMATION:` and `<ITEM>`, because both appear in
    EDGAR submissions.

    ***Refuses rather than answering "no" where the field is absent.*** A
    submission carrying neither marker raises `ResponseNotTheDocument`. The
    alternative — returning an empty list — would make *this parser does not
    understand the header* indistinguishable from *this filing is not an Item
    2.02 filing*, and the block would then quietly exclude every filing whose
    header shape is unfamiliar. **That is a refusal to score, and the reason it
    matters here is that the missing values would never appear in the
    denominator to be counted.**
    """

    if not any(m in submission_text for m in ITEM_MARKERS):
        raise ResponseNotTheDocument(
            "the submission carries neither 'ITEM INFORMATION:' nor '<ITEM>', "
            "so the Items it declares cannot be read.\n\n"
            "This is REFUSED and not answered 'no items'. An unreadable header "
            "and a filing with no matching item are different facts, and "
            "treating the first as the second would drop every filing whose "
            "header this parser does not understand, silently and out of the "
            "denominator."
        )

    codes: List[str] = []
    for line in submission_text.splitlines():
        stripped = line.strip()
        raw = ""
        if stripped.startswith("<ITEM>"):
            raw = stripped[len("<ITEM>"):]
        elif stripped.startswith("ITEM INFORMATION:"):
            raw = stripped[len("ITEM INFORMATION:"):]
        else:
            continue
        # The human header spells the item as a title; the machine header as a
        # number. Take the leading numeric token where there is one and record
        # the field verbatim otherwise, so nothing is invented.
        token = raw.strip().split()[0] if raw.strip() else ""
        if token and token[0].isdigit():
            codes.append(token.rstrip(".,"))
        elif raw.strip():
            codes.append(raw.strip())
    return codes


def declares_item(submission_text: str, item: str = EIGHTK_ITEM) -> bool:
    """Whether the submission declares `item`, by its numeric code only.

    The human header spells 2.02 as *Results of Operations and Financial
    Condition*, which this does NOT match on: a title is prose and matching it
    would be a string heuristic over language. Where only the title spelling is
    present the numeric code is absent and the filing is not selected, which is
    **under-selection and is stated as such** rather than repaired by pattern.
    """

    return any(c == item for c in item_codes(submission_text))


@dataclass(frozen=True)
class FetchedFiling:
    """One Form 4, raw and extracted, with everything the manifest records."""

    url: str
    cik: str
    company: str
    retrieved_at: str
    raw_bytes: int
    digest: str
    text: str

    @property
    def stem(self) -> str:
        return self.digest[:16]


def fetch_block(on: date, limit: int = BLOCK_SIZE) -> List[FetchedFiling]:
    """One block of Form 4 filings from one day's index.

    Refuses before it starts if ``SEC_CONTACT`` is unset: the identity is
    checked once here rather than per request, so the refusal arrives before
    anything is written rather than part-way through a block.
    """

    user_agent()  # refuse early, and loudly
    index_body, index_text = fetch(
        daily_index_url(on), MIN_INDEX_BYTES, INDEX_MARKER
    )
    rows = form4_rows(index_text)[:limit]
    if not rows:
        raise TraceCorpusRefused(
            f"{daily_index_url(on)} verified as an index and carries no Form 4 "
            "rows. That is a fact about the day, not a fetch failure, and it "
            "is reported rather than retried against another date chosen to "
            "produce a result."
        )
    out: List[FetchedFiling] = []
    for cik, company, path in rows:
        url = f"{SEC_HOST}/Archives/{path}"
        body, text = fetch(url, MIN_FORM4_BYTES, FORM4_MARKER)
        out.append(FetchedFiling(
            url=url,
            cik=cik,
            company=company,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            raw_bytes=len(body),
            digest=hashlib.sha256(body).hexdigest(),
            text=text,
        ))
    return out


def fetch_item_202_block(
    on: date, limit: int = BLOCK_SIZE, scan_ceiling: int = 500
) -> List[FetchedFiling]:
    """One block of 8-K **Item 2.02** filings from one day's index.

    **The re-pointed step-4 route** (`§12.1` P126). Refuses before it starts if
    `SEC_CONTACT` does not carry a usable identity: the identity is checked
    once here rather than per request, so the refusal arrives before anything
    is written rather than part-way through a block.

    **Two-stage, because the index does not carry the item.** The day's 8-K
    rows come from the field-delimited daily index; each submission is then
    fetched and its own SGML header read for the item. **`scan_ceiling` bounds
    how many submissions may be opened** looking for `limit` matches, and
    **exhausting it is a REFUSAL and not a short block**: a block of 61 items
    reported as though it were the day's Item 2.02 population is a denominator
    nobody chose.

    ***What this function does NOT do.*** It does not retry against another
    date, and it does not widen the item filter. *A day with too few Item 2.02
    filings is a fact about the day; a date chosen because it produced a full
    block is a sample chosen on its result.*
    """

    user_agent()  # refuse early, and loudly
    _index_body, index_text = fetch(
        daily_index_url(on), MIN_INDEX_BYTES, INDEX_MARKER
    )
    rows = eightk_rows(index_text)
    if not rows:
        raise TraceCorpusRefused(
            f"{daily_index_url(on)} verified as an index and carries no 8-K "
            "rows. That is a fact about the day, not a fetch failure, and it "
            "is reported rather than retried against another date chosen to "
            "produce a result."
        )

    out: List[FetchedFiling] = []
    opened = 0
    for cik, company, path in rows:
        if len(out) >= limit:
            break
        if opened >= scan_ceiling:
            raise TraceCorpusRefused(
                f"{scan_ceiling} submissions were opened from "
                f"{daily_index_url(on)} and {len(out)} carried Item "
                f"{EIGHTK_ITEM}, short of the {limit} a block requires.\n\n"
                "REFUSED rather than returning a short block. A block is the "
                "unit §9.4's stopping rule reads a defect rate over, and a "
                "partial one silently changes the denominator that rule "
                "divides by.\n\n"
                "Raise scan_ceiling deliberately, or fetch a second day and "
                "record that the block spans two."
            )
        url = f"{SEC_HOST}/Archives/{path}"
        body, text = fetch(url, MIN_8K_BYTES, SUBMISSION_MARKER)
        opened += 1
        if not declares_item(text):
            continue
        out.append(FetchedFiling(
            url=url,
            cik=cik,
            company=company,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            raw_bytes=len(body),
            digest=hashlib.sha256(body).hexdigest(),
            text=text,
        ))
    if len(out) < limit:
        raise TraceCorpusRefused(
            f"{daily_index_url(on)} yielded {len(out)} Item {EIGHTK_ITEM} "
            f"filings from {opened} 8-K submissions, short of {limit}.\n\n"
            "REFUSED rather than returning a short block, for the reason "
            "above: the block is the stopping rule's denominator."
        )
    return out


def write_manifest(filings: List[FetchedFiling], root: Path = CORPUS_ROOT) -> Path:
    """The manifest, in `corpora/us`'s own idiom: raw beside extracted.

    Extraction is destructive, so the raw response is retained and its digest
    recorded. `corpora/us` learned that the hard way: `raw_bytes` was a number
    with nothing behind it until the pages were kept.
    """

    raw_root = root / "_raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {NON_EVIDENTIARY}",
        "# Fenced corpus. No registration route may resolve here.",
        "url\tcik\tcompany\tretrieved_at\traw_bytes\tdigest",
    ]
    for f in filings:
        (raw_root / f"{f.stem}.xml").write_text(f.text, encoding="utf-8")
        lines.append(
            f"{f.url}\t{f.cik}\t{f.company}\t{f.retrieved_at}\t"
            f"{f.raw_bytes}\t{f.digest}"
        )
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "_manifest.tsv"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest
