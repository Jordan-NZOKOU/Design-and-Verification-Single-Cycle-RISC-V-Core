#!/usr/bin/env bash
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

# Build the complete English project report from the committed XeLaTeX source.
#
# Engineering intent:
#   1. resolve every path from this script rather than the caller's directory;
#   2. regenerate diagrams before compilation so figures cannot silently drift;
#   3. start from a clean LaTeX state to expose missing dependencies;
#   4. run deterministic XeLaTeX passes so references, TOC, LOF, and LOT converge;
#   5. copy only the release PDF into the documentation directory;
#   6. remove all auxiliary files so a clean Git worktree remains after a build.
#
# Usage:
#   ./scripts/build_report.sh
#
# Required tools:
#   python3, inkscape, xelatex
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/00_documentation/report_source"
SOURCE_TEX="nexvantis_rv32i_single_cycle_report.tex"
SOURCE_PDF="${SOURCE_DIR}/nexvantis_rv32i_single_cycle_report.pdf"
RELEASE_PDF="${ROOT_DIR}/00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf"

# Fail early with a clear message rather than allowing a nested command to fail
# with an ambiguous "command not found" status.
for required_tool in python3 inkscape xelatex; do
    if ! command -v "${required_tool}" >/dev/null 2>&1; then
        echo "Error: required tool '${required_tool}' was not found in PATH." >&2
        exit 127
    fi
done

# Figures are source-controlled, but the report build deliberately regenerates
# them to prove the committed generator still reproduces all required assets.
python3 "${ROOT_DIR}/scripts/generate_diagrams.py"

# The cleanup trap runs after success or failure. It removes only generated
# LaTeX intermediates; the committed .tex source and copied release PDF remain.
cleanup_latex() {
    (
        cd "${SOURCE_DIR}"
        rm -f -- *.aux *.fdb_latexmk *.fls *.lof *.log *.lol *.lot \
            *.out *.toc *.xdv nexvantis_rv32i_single_cycle_report.pdf
    )
}
trap cleanup_latex EXIT

(
    cd "${SOURCE_DIR}"

    # Remove stale cross-reference files before building. This makes the build
    # deterministic and prevents a previous report layout from masking errors.
    rm -f -- *.aux *.fdb_latexmk *.fls *.lof *.log *.lol *.lot \
        *.out *.toc *.xdv nexvantis_rv32i_single_cycle_report.pdf

    # Two explicit XeLaTeX passes stabilize the table of contents, figure/list
    # references, and long-table widths without depending on persistent state.
    for pass in 1 2; do
        echo "XeLaTeX pass ${pass}/2"
        xelatex \
            -interaction=nonstopmode \
            -halt-on-error \
            -file-line-error \
            "${SOURCE_TEX}" >/dev/null
    done
)

if [[ ! -s "${SOURCE_PDF}" ]]; then
    echo "Error: report compilation completed without producing a non-empty PDF." >&2
    exit 1
fi

# Install the release artifact atomically so readers never observe a partial PDF.
temporary_release="${RELEASE_PDF}.tmp"
cp "${SOURCE_PDF}" "${temporary_release}"
mv "${temporary_release}" "${RELEASE_PDF}"

# Set stable, explicit document metadata without changing visible report content.
python3 - "${RELEASE_PDF}" <<'PY'
from pathlib import Path
import sys
import fitz

path = Path(sys.argv[1])
document = fitz.open(path)
metadata = document.metadata or {}
metadata.update(
    {
        "title": "Nexvantis - RV32I Single-Cycle Processor in Verilog",
        "author": "Jordan Nzokou and Doeg Tiozang",
        "subject": "Complete English RTL design and verification report",
        "keywords": "Nexvantis, RISC-V, RV32I, Verilog, RTL, verification",
        "creator": "Nexvantis XeLaTeX report build",
        "producer": "XeLaTeX with PyMuPDF metadata normalization",
    }
)
document.set_metadata(metadata)
temporary = path.with_suffix(".metadata.pdf")
document.save(temporary, garbage=4, deflate=True)
document.close()
temporary.replace(path)
PY

page_count="$(python3 - "${RELEASE_PDF}" <<'PY'
import sys
import fitz
with fitz.open(sys.argv[1]) as document:
    print(document.page_count)
PY
)"

echo "Report built successfully: ${RELEASE_PDF} (${page_count} pages)"
