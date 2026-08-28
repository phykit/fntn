"""The §9.4 trace corpus: SEC **8-K Item 2.02** filings, fetched and verified.

**What this is for.** §14's trace precondition requires §9.4's harness run to
its stopping rule *"including a minimum sample of the primary catalyst family's
live filing flow"*. **The primary catalyst family is `earnings_event` and the
flow is 8-K Item 2.02**, *Results of Operations and Financial Condition*.
`corpora/us` is rule text and exercises the machinery; only the family's own
flow exercises the family.

***RE-POINTED 27 August 2026 from Form 4, and the module said so of itself
before it did so.*** §0 decision retired `insider_dealing`, `§12.1` P126
re-pointed binding-path step 4 at Item 2.02, and **this module went on fetching
Form 4 for a day and a batch.** *Its own docstring carried the reason step 4
rejected Form 4* -- **"Form 4 is a field-delimited regulatory form, so even the
clerk is replaced by a parser"** -- *and the whole ground for choosing Item 2.02
is that it is the ONLY candidate exercising the model-mediated extraction path,
which is the path rule 1 is written against.* **A fetcher pointed at the form
its own docstring gives the reason for rejecting is `docs/CORRECTIONS.md` B17.**

**What this is NOT for, and the containment is the point.** An 8-K names an
issuer and a period of report, and its release carries dated figures. **That is
precisely the material the entity fence exists to keep out of a proposal.**
This corpus is
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

***THE CLERK IS NOT INVOLVED IN THE FETCH, AND IS THE WHOLE POINT OF THE
CORPUS.*** Nothing in this module calls a model: the daily index, the
submission header and the document manifest are all field-delimited, so per
CLAUDE.md's first rule they are read by a parser. **What the corpus is FOR is
the step after this one**, where §3.5's extraction reads free-form prose with a
schema-enforced model call. *Item 2.02 was chosen because that step is the
weakest part of the machinery and a trace belongs where the machinery is
weakest.*

**The cost of that choice, restated here so a reader of the results meets it
first:** Item 2.02 is **furnished, not filed**; the release is free-form, so
**the refusal rate at `extraction_schema_incomplete` will be higher than a
field-delimited form's and must not be read as a machinery defect**; and
Regulation G's non-GAAP reconciliation makes the extraction genuinely hard.
***That difficulty is the reason for choosing it and will look like a fault.***
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
MIN_INDEX_BYTES = 4000
#: The submission header is a small SGML block. Below this it is not one.
MIN_HEADER_BYTES = 500
#: A press release below this is not a press release. **Weaker than the Form 4
#: floor was, and it has to be**: see `verify_prose_response`.
MIN_RELEASE_BYTES = 1000

#: The structural markers. A response without its marker is **reported as the
#: failure it is** and never worked around.
INDEX_MARKER = "Form Type"
HEADER_MARKER = "<ACCESSION-NUMBER>"

#: The form and the item. **Both are registered decisions and neither is a
#: default**: the family is §13 row 22's `earnings_event` and the flow is fixed
#: by `§12.1` P126.
FORM_TYPE = "8-K"

#: §13 row 12's form. **A separate constant beside the 8-K one and not a
#: replacement for it**: step 4's trace corpus is Item 2.02 by P126 and stays
#: there, because a field-delimited form exercises a parser and not the
#: model-mediated extraction path §9.4 is aimed at. **Row 12 wants exactly the
#: property that disqualified Form 4 from the trace**: it is machine-parseable,
#: so the qualifying rate is a deterministic read rather than an estimate.
FORM4_TYPE = "4"

#: The structural marker for a Form 4 primary document. **A positive marker and
#: not a byte floor**, per `verify_response`'s contract: a response shaped like
#: a page rather than a document fails this whatever its size.
FORM4_MARKER = "<ownershipDocument"

#: A Form 4 XML below this is not a Form 4.
FORM4_MIN_BYTES = 500
TARGET_ITEM = "2.02"
#: Item 2.02's title as EDGAR writes it in the full submission's
#: ``ITEM INFORMATION`` lines. **Carried but NOT used as the filter**: the
#: `-index-headers.html` view gives item NUMBERS, which cannot drift with a
#: wording change, and a number is the stabler key.
TARGET_ITEM_TITLE = "Results of Operations and Financial Condition"

#: Document types that carry the release, most preferred first. **An 8-K body
#: is the last resort and not the first choice**: Item 2.02 furnishes the
#: release as an exhibit and the body typically incorporates it by reference,
#: so taking the body would retain a cross-reference where the corpus needs
#: prose with figures in it.
RELEASE_TYPES = ("EX-99.1", "EX-99", "EX-99.2", "8-K")

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
            body = _decoded(response.read(), response.headers.get("Content-Encoding"))
    except urllib.error.HTTPError as exc:
        raise ResponseNotTheDocument(
            f"{url} returned HTTP {exc.code} {exc.reason}. Reported rather "
            f"than retried into a placeholder."
        ) from exc
    return body, verify_response(url, body, minimum, marker)


def _decoded(body: bytes, content_encoding: Optional[str]) -> bytes:
    """Undo the transfer encoding the request asked for.

    ***This did not exist until 27 August 2026, and its absence meant the
    fetcher had never worked.*** The request has always sent
    ``Accept-Encoding: gzip, deflate`` and `urllib` **does not decompress**:
    unlike `curl` and unlike `requests`, it hands back the compressed bytes and
    leaves `Content-Encoding` on the response for the caller to act on. So the
    daily index arrived as 102,195 bytes of gzip, the structural marker was
    absent from it, and `verify_response` correctly reported *the response was
    not the document*.

    **The guard was right and the transport was wrong**, which is the harder
    version of this failure to diagnose: nothing was broken at the point the
    error named.

    ***Why it survived to the first live run.*** `SEC_CONTACT` was unset for the
    whole life of this module, so `user_agent()` refused before a single
    request was made, and **every test of the fetch path supplied bytes
    directly to `verify_response`.** *The transport had never been exercised
    against a server at all.* It is `docs/CORRECTIONS.md` B17's second half and
    the same class as the first: **a dependency's contract assumed rather than
    read**, here `urllib`'s, and found by running the thing.

    *Refusing an encoding the caller cannot undo, rather than decompressing it,
    was considered and rejected: it would push the cost of this module's
    convenience onto a regulator's bandwidth for a hundred requests a block.*
    """

    if not content_encoding:
        return body
    encoding = content_encoding.strip().lower()
    if encoding == "gzip":
        import gzip
        return gzip.decompress(body)
    if encoding == "deflate":
        import zlib
        try:
            return zlib.decompress(body)
        except zlib.error:
            # Raw deflate without a zlib wrapper: a documented variant, and
            # distinguished here rather than caught and returned as-is.
            return zlib.decompress(body, -zlib.MAX_WBITS)
    if encoding == "identity":
        return body
    raise ResponseNotTheDocument(
        f"the response carries Content-Encoding {content_encoding!r}, which "
        "this module cannot undo. Reported rather than returned undecoded: "
        "undecoded bytes would fail the structural marker and the error would "
        "name the document when the fault is the transport."
    )


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


def form_rows(index_text: str, form_type: str) -> List[Tuple[str, str, str]]:
    """(CIK, company, path) for every row of one form type in a daily index.

    **Generalised 28 August 2026 so §13 row 12 can reach Form 4.** The parser
    was already form-agnostic in everything except one comparison against a
    module constant; `eight_k_rows` now calls this with `FORM_TYPE` and its
    behaviour is unchanged, so step 4's corpus is untouched.

    ***The form type is an ARGUMENT and not a second constant.*** A module
    constant deciding which population a fetch returns is the defect class that
    caused the `agent_model`, `lexicon`, `rulebook_stopwords` and intake-budget
    re-stamps: a value that changes what a run produces while moving nothing on
    the record. Here it is passed at the call site and recorded in the manifest.
    """

    out: List[Tuple[str, str, str]] = []
    for line in index_text.splitlines():
        parts = line.rsplit(None, 3)
        if len(parts) != 4:
            continue
        head, cik, _filed, path = parts
        if not cik.isdigit() or not path.endswith(".txt"):
            continue
        form, _, company = head.partition(" ")
        if form.strip() != form_type:
            continue
        out.append((cik, company.strip(), path))
    return out


def eight_k_rows(index_text: str) -> List[Tuple[str, str, str]]:
    """(CIK, company, path) for every 8-K in a daily form index.

    A deterministic parser over a field-delimited file, per CLAUDE.md's first
    rule. The index is fixed-width with a dashed rule under the header; rows
    are split on runs of whitespace from the right, because a company name
    contains spaces and the three fields after it do not.

    **`8-K/A` is excluded and that is a decision.** An amendment restates or
    corrects an earlier furnishing, so its ingestion lag is measured against
    the amendment's own date and says nothing about how promptly the ORIGINAL
    reached this system, which is what §13 row 15 is short of. *Including them
    would put a second population in the same denominator.*
    """

    return form_rows(index_text, FORM_TYPE)


def header_url(path: str) -> str:
    """The submission's own header view, from its `.txt` path in the index.

    **Why this and not the full submission.** The `.txt` carries every document
    in the filing and runs to megabytes; the header view is a few kilobytes and
    carries **the item numbers and the document manifest**, which is everything
    the filter and the release selection need. *`Range` requests were probed
    against sec.gov and are not honoured: the server returns 200 with the whole
    body, so a range would have downloaded the megabytes and discarded them.*

    ``edgar/data/2064314/0001213900-26-093981.txt`` becomes
    ``edgar/data/2064314/000121390026093981/0001213900-26-093981-index-headers.html``.
    """

    stem = path.rsplit("/", 1)[-1]
    if not stem.endswith(".txt"):
        raise TraceCorpusRefused(
            f"{path!r} is not a submission text path, so no header view can be "
            "derived from it. Refused rather than guessed at."
        )
    accession = stem[: -len(".txt")]
    directory = path.rsplit("/", 1)[0]
    return (
        f"{SEC_HOST}/Archives/{directory}/{accession.replace('-', '')}/"
        f"{accession}-index-headers.html"
    )


def parse_header(header_text: str) -> Tuple[List[str], List[Tuple[str, str, str]]]:
    """(item numbers, documents) from a submission header view.

    Returns item numbers such as ``2.02`` and documents as
    ``(type, filename, description)``. **Both sections are SGML tags**, the
    document list HTML-escaped because the header view wraps the raw header in
    a comment and then repeats it inside a ``<PRE>`` block.

    *A parser and not a model, because both are field-delimited.*
    """

    text = header_text.replace("&lt;", "<").replace("&gt;", ">")
    items = [
        line[len("<ITEMS>"):].strip()
        for line in text.splitlines()
        if line.startswith("<ITEMS>")
    ]
    documents: List[Tuple[str, str, str]] = []
    current: dict = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "<DOCUMENT>":
            current = {}
        elif stripped == "</DOCUMENT>":
            if current.get("FILENAME"):
                documents.append((
                    current.get("TYPE", ""),
                    current["FILENAME"],
                    current.get("DESCRIPTION", ""),
                ))
            current = {}
        else:
            for tag in ("TYPE", "FILENAME", "DESCRIPTION"):
                if stripped.startswith(f"<{tag}>") and tag not in current:
                    current[tag] = stripped[len(tag) + 2:].strip()
    # De-duplicate: the header view carries the manifest twice, once in the
    # leading comment and once inside <PRE>. Order-preserving, first wins.
    seen = set()
    unique = []
    for doc in documents:
        if doc[1] in seen:
            continue
        seen.add(doc[1])
        unique.append(doc)
    return items, unique


def select_release(documents: List[Tuple[str, str, str]]) -> str:
    """The filename of the document carrying the release. **Refuses.**

    Preference order is `RELEASE_TYPES`. **An 8-K with no exhibit and no body
    is refused rather than skipped silently**: the corpus records what it could
    not take, because a filing quietly dropped is a filing missing from a
    denominator §9.4 computes a rate over.
    """

    for wanted in RELEASE_TYPES:
        for doc_type, filename, _desc in documents:
            if doc_type.upper() == wanted:
                return filename
    raise TraceCorpusRefused(
        "this filing's manifest carries no document of any type in "
        f"{RELEASE_TYPES}, so there is nothing to take as the release. "
        "Reported rather than skipped: a filing dropped without a record is a "
        "filing missing from a denominator."
    )


def verify_prose_response(url: str, body: bytes, minimum: int) -> str:
    """A byte floor and a stub check, and **NO positive structural marker.**

    ***This guarantee is weaker than `verify_response`'s and the difference is
    stated rather than papered over.*** A Form 4 carries
    ``<ownershipDocument``; an earnings release is free-form prose and **has no
    structural token that every instance carries and no error page could**.
    Inventing one -- a `<html` tag, a keyword such as *earnings* -- would be a
    check that passes on EDGAR's own error page or fails on a valid release,
    and either is worse than saying what is and is not established.

    **What IS established, and it is a real control rather than a shrug:** the
    filename was read from **the regulator's own document manifest for this
    accession**, so a 200 on that exact path is the document by construction
    unless the server substituted something. *The floor and the stub markers
    catch the substitution this project has actually observed.*

    **What is NOT established:** that the prose is a Results-of-Operations
    release rather than some other exhibit. **That is the item filter's job**,
    and the item filter reads item NUMBERS from the header, which is
    field-delimited and cannot drift.
    """

    if len(body) < minimum:
        raise ResponseNotTheDocument(
            f"{url} returned {len(body)} bytes, below the {minimum}-byte floor. "
            "A previous session recorded sec.gov serving a 698-byte stub with "
            "a 200 status, which is this failure. It is reported rather than "
            f"worked around.\n\nFirst 200 bytes: {body[:200]!r}"
        )
    text = body.decode("utf-8", errors="replace")
    lowered = text[:4000].lower()
    for stub in ("<title>sec.gov | request rate threshold exceeded",
                 "your request rate has exceeded",
                 "<title>sec.gov | file not found"):
        if stub in lowered:
            raise ResponseNotTheDocument(
                f"{url} returned {len(body)} bytes of EDGAR's own error page, "
                f"not the document. Matched {stub!r}. Reported, and the block "
                "stops rather than continuing at a rate the server has already "
                "refused."
            )
    return text


@dataclass(frozen=True)
class FetchedFiling:
    """One filing, raw and extracted, with everything the manifest records."""

    url: str
    cik: str
    company: str
    retrieved_at: str
    raw_bytes: int
    digest: str
    text: str
    #: Every item the filing declares, not only the one filtered on. A filing
    #: furnishing 2.02 alongside 9.01 is a different object from one furnishing
    #: 2.02 alone, and §9.4 stratifies.
    items: str = ""
    accession: str = ""
    #: How many 8-Ks were examined to reach this one, and how many the day
    #: carried. **A yield with no denominator is not a yield.**
    scanned: int = 0
    candidates: int = 0

    @property
    def stem(self) -> str:
        return self.digest[:16]


def fetch_block(on: date, limit: int = BLOCK_SIZE,
                pause_s: float = 0.15) -> List[FetchedFiling]:
    """One block of 8-K **Item 2.02** filings from one day's index.

    Refuses before it starts if ``SEC_CONTACT`` is unset: the identity is
    checked once here rather than per request, so the refusal arrives before
    anything is written rather than part-way through a block.

    **Three fetches per kept filing and one per candidate**, which is the cost
    of filtering on the item: the daily index does not carry item numbers, so
    every 8-K's header is read and most are discarded. *`pause_s` is a
    courtesy to a regulator's server and not a rate limit this code enforces
    against itself; the SEC publishes a ceiling and this sits well under it.*

    **`scanned` is returned on every filing** so the manifest records how many
    8-Ks were examined to yield the block. A rate over items 2.02 computed
    against the number kept, with the number examined unrecorded, is a rate
    whose denominator nobody can reconstruct.
    """

    import time

    user_agent()  # refuse early, and loudly
    _body, index_text = fetch(
        daily_index_url(on), MIN_INDEX_BYTES, INDEX_MARKER
    )
    rows = eight_k_rows(index_text)
    if not rows:
        raise TraceCorpusRefused(
            f"{daily_index_url(on)} verified as an index and carries no "
            f"{FORM_TYPE} rows. That is a fact about the day, not a fetch "
            "failure, and it is reported rather than retried against another "
            "date chosen to produce a result."
        )

    out: List[FetchedFiling] = []
    scanned = 0
    for cik, company, path in rows:
        if len(out) >= limit:
            break
        scanned += 1
        header_body, header_text = fetch(
            header_url(path), MIN_HEADER_BYTES, HEADER_MARKER
        )
        items, documents = parse_header(header_text)
        if TARGET_ITEM not in items:
            time.sleep(pause_s)
            continue
        filename = select_release(documents)
        directory = path.rsplit("/", 1)[0]
        accession = path.rsplit("/", 1)[-1][: -len(".txt")]
        url = (
            f"{SEC_HOST}/Archives/{directory}/"
            f"{accession.replace('-', '')}/{filename}"
        )
        body = fetch_raw(url)
        text = verify_prose_response(url, body, MIN_RELEASE_BYTES)
        out.append(FetchedFiling(
            url=url,
            cik=cik,
            company=company,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            raw_bytes=len(body),
            digest=hashlib.sha256(body).hexdigest(),
            text=text,
            items=",".join(items),
            accession=accession,
            scanned=scanned,
            candidates=len(rows),
        ))
        time.sleep(pause_s)
    if not out:
        raise TraceCorpusRefused(
            f"{scanned} {FORM_TYPE} filings were examined on {on} and none "
            f"carried Item {TARGET_ITEM}. Reported as a fact about the day. "
            "Nothing is retried against another date chosen to produce a "
            "result, and nothing is written."
        )
    # **Stamp the FINAL scan count on every filing, not the count at the moment
    # each was kept.** Each row carried the running total as at its own append,
    # so the first row held the smallest of them, and the manifest reported the
    # yield of the whole block against the denominator of its first hit: on the
    # smoke run, *8 of 161 examined to yield 3*, when 8 was where the first hit
    # landed. **A denominator that is a prefix of itself is worse than none**,
    # because it reads as a measurement.
    import dataclasses
    return [dataclasses.replace(f, scanned=scanned) for f in out]


def fetch_raw(url: str, timeout: int = 30) -> bytes:
    """One GET, identified, with NO structural verification. See its caller.

    Split out from `fetch` deliberately: `fetch` takes a marker because every
    document it retrieves has one, and a prose release does not. **Rather than
    passing a marker that would be a lie, the verification is a separate call
    the caller makes explicitly**, so a reader can see which of the two
    guarantees any given document carries.
    """

    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent(),
        "Accept-Encoding": "gzip, deflate",
        "Host": url.split("/")[2],
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _decoded(response.read(), response.headers.get("Content-Encoding"))
    except urllib.error.HTTPError as exc:
        raise ResponseNotTheDocument(
            f"{url} returned HTTP {exc.code} {exc.reason}. Reported rather "
            "than retried into a placeholder."
        ) from exc


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
        f"# form {FORM_TYPE}, item {TARGET_ITEM} ({TARGET_ITEM_TITLE})",
        f"# {filings[0].scanned if filings else 0} of "
        f"{filings[0].candidates if filings else 0} {FORM_TYPE} filings on the "
        f"day were examined to yield {len(filings)}. A yield with no "
        f"denominator is not a yield.",
        "url\tcik\tcompany\taccession\titems\tretrieved_at\traw_bytes\tdigest",
    ]
    for f in filings:
        # `.html`, not `.xml`. The retained raw is a press release, and naming
        # it after the form the fetcher used to take would be a filename
        # asserting a shape the bytes do not have.
        (raw_root / f"{f.stem}.html").write_text(f.text, encoding="utf-8")
        lines.append(
            f"{f.url}\t{f.cik}\t{f.company}\t{f.accession}\t{f.items}\t"
            f"{f.retrieved_at}\t{f.raw_bytes}\t{f.digest}"
        )
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "_manifest.tsv"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# §13 row 12: Form 4 flow. Same transport, same guard, a different population.
# ---------------------------------------------------------------------------


def extract_ownership_document(submission_text: str) -> Optional[str]:
    """The Form 4 XML out of a full submission `.txt`.

    **One fetch per filing rather than three.** The 8-K path reads a header view
    to filter on item numbers, because the daily index does not carry them.
    Form 4 needs no such filter: every row of the index that says `4` is the
    population, so the submission text is fetched once and the primary document
    lifted out of it.

    Returns ``None`` where no ownership document is present, which is a fact
    about the submission and not a fetch failure. **A paper filing and a
    submission whose primary document is a PDF both land here**, and both are
    reported as skipped rather than counted as filings that failed a test.
    """

    start = submission_text.find(FORM4_MARKER)
    if start == -1:
        return None
    end = submission_text.find("</ownershipDocument>", start)
    if end == -1:
        return None
    return submission_text[start:end + len("</ownershipDocument>")]


def fetch_form4_block(on: date, limit: int = BLOCK_SIZE,
                      pause_s: float = 0.15,
                      out_dir: Optional[Path] = None) -> Tuple[int, int, Path]:
    """One day's Form 4 flow, written as XML for `row12.read_directory`.

    Returns ``(kept, scanned, directory)``. **Both counts are returned and both
    are written**, because §13 row 12 is a rate and a rate whose denominator
    nobody can reconstruct is not a measurement. *`scanned` is every Form 4 row
    in the index; `kept` is those whose submission carried an ownership
    document.*

    **Refuses before it starts if `SEC_CONTACT` is unset or is a placeholder.**
    The identity is checked once, here, so the refusal arrives before anything
    is written rather than part-way through a block.

    ***This does not touch step 4's corpus.*** It writes to its own directory,
    underscore-prefixed so `Corpus.__post_init__` refuses to build a
    registration row pointing at it and `corpusio` will not read it as a
    discovery corpus. **Row 12's population is a measurement input and must
    never become material an agent is shown.**
    """

    import time

    user_agent()  # refuse early, and loudly
    root = Path(out_dir) if out_dir else Path("corpora/_form4") / on.isoformat()
    root.mkdir(parents=True, exist_ok=True)

    _body, index_text = fetch(daily_index_url(on), MIN_INDEX_BYTES, INDEX_MARKER)
    rows = form_rows(index_text, FORM4_TYPE)
    if not rows:
        raise TraceCorpusRefused(
            f"{daily_index_url(on)} verified as an index and carries no "
            f"form {FORM4_TYPE!r} rows. That is a fact about the day, not a "
            "fetch failure, and it is reported rather than retried against "
            "another date chosen to produce a result."
        )

    kept = scanned = 0
    for cik, _company, path in rows:
        if kept >= limit:
            break
        scanned += 1
        accession = path.rsplit("/", 1)[-1][: -len(".txt")]
        raw = fetch_raw(f"{SEC_HOST}/Archives/{path}")
        xml = extract_ownership_document(raw.decode("utf-8", errors="replace"))
        if xml is None or len(xml) < FORM4_MIN_BYTES:
            time.sleep(pause_s)
            continue
        (root / f"{accession}.xml").write_text(xml)
        kept += 1
        time.sleep(pause_s)

    (root / "_manifest.tsv").write_text(
        "form_type\tindex_date\tscanned\tkept\tretrieved_at\n"
        f"{FORM4_TYPE}\t{on.isoformat()}\t{scanned}\t{kept}\t"
        f"{datetime.now(timezone.utc).isoformat()}\n"
    )
    return kept, scanned, root
