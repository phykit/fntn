"""Archive-side data. **Forbidden to the discovery layer by name.**

``fntn.data`` is one of `fences.FORBIDDEN_TO_DISCOVERY`, and this package is
placed here for exactly that reason rather than under ``fntn.scanner``.

**A delisting is an OUTCOME.** A register of which names left the market is
outcome-adjacent material: an agent that could read it could select mechanisms
on survival, which is the contamination §3.7's import fence exists against. A
module of the same content sitting in ``fntn.scanner`` would be reachable by
`discovery.py` **without tripping any fence**, because the fence matches module
names and would have had no name to match.

*Placing it where the fence can see it is the whole design decision, and it
costs a package nobody would otherwise create.*

**And it makes the REVERSE fence applicable for the first time.**
`assert_reverse_import_fence` returned ``NOT_APPLICABLE`` while none of the
forbidden modules existed. This package is the first one to exist, so the check
now walks a real closure and returns ``CLEAN`` or raises. *A fence that has
never had anything to walk is a fence nobody has tested.*
"""
