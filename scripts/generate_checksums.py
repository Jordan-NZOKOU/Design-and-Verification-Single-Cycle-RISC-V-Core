#!/usr/bin/env python3
# Copyright 2026 Jordan Nzokou and Doeg Tiozang
# Project: Nexvantis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate the deterministic SHA-256 inventory for the Nexvantis repository.

The checksum file is a release artifact. It is intentionally generated only
after documentation, diagrams, and the report are final. The output excludes
itself and transient build directories so repeated invocations remain stable.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "00_documentation" / "SHA256SUMS.txt"

NOTICE = """# Copyright 2026 Jordan Nzokou and Doeg Tiozang
# Project: Nexvantis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SHA-256 inventory. Paths are relative to the repository root.

"""

# These names are never release inputs. Excluding them prevents local simulator
# or language-tool caches from making the inventory machine-dependent.
EXCLUDED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "build",
    "work",
    "_minted-report",
}
EXCLUDED_SUFFIXES = {
    ".aux",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".lol",
    ".lof",
    ".lot",
    ".out",
    ".pyc",
    ".toc",
    ".vcd",
    ".vvp",
    ".wlf",
    ".xdv",
}
EXCLUDED_NAMES = {"transcript", "vsim.wlf"}


def sha256(path: Path) -> str:
    """Hash one file in bounded chunks so large PDFs do not require extra RAM."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_release_file(path: Path, output: Path) -> bool:
    """Return whether *path* belongs in the deterministic release inventory."""

    if not path.is_file() or path.resolve() == output.resolve():
        return False
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
        return False
    if path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def parse_args() -> argparse.Namespace:
    """Expose a small CLI so release automation may select another output path."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Checksum destination (default: 00_documentation/SHA256SUMS.txt)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(
        (path for path in ROOT.rglob("*") if is_release_file(path, output)),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )

    # Use the conventional two-space separator understood by sha256sum -c.
    lines = [
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}"
        for path in files
    ]
    output.write_text(NOTICE + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(files)} checksums to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
