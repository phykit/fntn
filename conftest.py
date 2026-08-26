"""Make `fntn` importable from a bare clone, without an editable install.

`pythonpath` in pyproject.toml covers pytest; this covers a plain `python -c`
or an editor's test runner. Both point at the same src layout.
"""

import sys
from pathlib import Path

src = Path(__file__).parent / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))
