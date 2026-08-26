#!/usr/bin/env bash
# Tidy the fntn working tree after unpacking the transfer archive.
# Idempotent. Verifies before acting. Moves rather than deletes, except where
# a file is proven byte-identical to the copy that is staying.
set -euo pipefail
 
cd "$(git rev-parse --show-toplevel)"
echo "repo: $(pwd)"
echo "branch: $(git branch --show-current)"
echo
 
STRAY_DIR="../fntn_strays"
moved=0
 
# --- 1. Transport artefacts. Never commit a bundle or a zip of the repo. ----
shopt -s nullglob
for f in *.bundle *.zip; do
  mkdir -p "$STRAY_DIR"
  echo "moving transport artefact out of the tree: $f -> $STRAY_DIR/"
  mv -n "$f" "$STRAY_DIR/"
  moved=$((moved+1))
done
shopt -u nullglob
 
# --- 2. Duplicate spec at root. Only remove it if it is byte-identical. -----
ROOT_SPEC="from_narrative_to_null_v1_13.md"
CANON_SPEC="docs/spec/from_narrative_to_null_v1_13.md"
if [[ -f "$ROOT_SPEC" ]]; then
  if [[ ! -f "$CANON_SPEC" ]]; then
    echo "docs/spec copy missing; promoting the root copy into place"
    mkdir -p docs/spec && mv "$ROOT_SPEC" "$CANON_SPEC"
  elif cmp -s "$ROOT_SPEC" "$CANON_SPEC"; then
    echo "root spec is byte-identical to $CANON_SPEC; removing the duplicate"
    rm "$ROOT_SPEC"
  else
    mkdir -p "$STRAY_DIR"
    echo "WARNING: root spec DIFFERS from $CANON_SPEC. Not guessing which wins."
    echo "         moved to $STRAY_DIR/ for you to diff. docs/spec is unchanged."
    mv -n "$ROOT_SPEC" "$STRAY_DIR/"
    moved=$((moved+1))
  fi
fi
 
# --- 3. .gitignore: keep caches and transport artefacts out permanently. ----
touch .gitignore
for pat in '__pycache__/' '*.pyc' '*.db' '.pytest_cache/' '*.bundle' 'fntn_repo.zip' '.venv/'; do
  grep -qxF "$pat" .gitignore || { echo "$pat" >> .gitignore; echo "gitignore += $pat"; }
done
git rm -r --cached --quiet .pytest_cache 2>/dev/null || true
 
# --- 4. Verify the tree is what it should be. ------------------------------
echo
missing=0
for p in CLAUDE.md README.md conftest.py pyproject.toml \
         docs/OPEN_ITEMS.md docs/CONVENTIONS.md "$CANON_SPEC" \
         src/fntn/__init__.py src/fntn/scanner/codes.py \
         src/fntn/scanner/records.py src/fntn/scanner/fences.py \
         src/fntn/scanner/ingest.py src/fntn/scanner/screen.py \
         src/fntn/scanner/segment.py src/fntn/scanner/discovery.py \
         src/fntn/scanner/ledger.py src/fntn/scanner/summaries.py \
         src/fntn/scanner/trace.py src/fntn/scanner/run.py \
         tests/test_scanner.py; do
  [[ -f "$p" ]] || { echo "MISSING: $p"; missing=$((missing+1)); }
done
if (( missing )); then
  echo
  echo "$missing expected file(s) missing. Stopping before commit: an incomplete"
  echo "tree committed is harder to unpick than one left dirty."
  exit 1
fi
echo "structure: all expected files present"
 
# --- 5. Tests must pass before anything is committed. ----------------------
echo
PY=$(command -v python3 || command -v python)
 
# Distinguish "the harness is absent" from "the tests failed". Reporting the
# second when the first is true is a message asserting a cause it has not
# verified, which is the failure class this codebase is built against.
if ! "$PY" -c "import pytest" 2>/dev/null; then
  echo "pytest is not installed for $PY, so no test has run and none has failed."
  echo "Install it and re-run this script (it is idempotent):"
  echo
  echo "    pip install -q pytest && bash \"$0\""
  echo
  echo "Nothing committed."
  exit 2
fi
 
if ! "$PY" -m pytest tests/ -q; then
  echo
  echo "Tests ran and failed. Nothing committed. If the failure is"
  echo "test_every_defined_code_is_emitted, a reason code exists with no branch"
  echo "that reaches it; any other failure, read the assertion."
  exit 1
fi
 
# --- 6. Stage and commit. Push is left to you. -----------------------------
echo
git add -A
if git diff --cached --quiet; then
  echo "nothing to commit; tree already clean"
else
  git -c user.email=noreply@anthropic.com -c user.name=Claude \
      commit -q -m "Add the agent discovery layer, spec v1.13 and the Claude Code scaffold
 
Unpacked from the transfer archive. Transport artefacts and caches excluded.
 
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
  echo "committed:"
  git log --oneline -1
fi
 
echo
echo "--- status ---"
git status --short
echo
(( moved )) && echo "$moved stray file(s) moved to $STRAY_DIR (outside the repo)"
echo "next: git push -u origin main"
 