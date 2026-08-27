# Reconciliation, 27 August 2026, third pass

Written **before** any work in the ten-phase batch, under CLAUDE.md's session
protocol. Each statement names the command that establishes it.

## 1. Tree, branch, push state

```
$ git status --porcelain            (empty)
$ git rev-parse --abbrev-ref HEAD   fence-and-corpus-repairs
$ git log --oneline origin/fence-and-corpus-repairs..HEAD   (empty)
$ python -m pytest tests/ -q        259 passed
```

**Clean, nothing unpushed on the working branch, 259 passing**, matching
`CLAUDE.md`.

## 2. The finding this pass was called to check, and it is confirmed

```
$ git rev-parse origin/main
44ee009dfef7e743dff4d57e190e76743cfc9ee6
$ git log --oneline -1 origin/main
44ee009 Remove build artefacts and a stray file from the tree
$ git rev-list --count origin/main..HEAD
33
```

**`origin/main` is thirty-three commits behind.** Every §12.1 row from P84 to
P100, the discovery layer's fences, the run report, the trace corpus, the two
decision files and the derived clip floor are on
`fence-and-corpus-repairs` and **on no branch the operator's other surfaces
watch**. The work is pushed and it is not visible.

**This is the protocol's own failure mode one level up.** The rule says an
unpushed commit in a Codespace is not a record. The corollary this pass adds:
**a commit pushed to a branch nothing watches is not a record either.** The
session protocol will be amended to say so.

## 3. What phase 0 must not do

**No squash.** The §12.1 discipline makes the commit sequence the change log,
one commit per P-row, and a squash destroys the correspondence. A merge commit
preserves it.

## 4. Phase order, and where this pass expects to stop

Phases 0 to 3 are load-bearing. Phase 5 is gated on `SEC_CONTACT`, which was
unset at the last check and is expected to remain so, in which case phase 5
refuses and stops rather than substituting anything.
