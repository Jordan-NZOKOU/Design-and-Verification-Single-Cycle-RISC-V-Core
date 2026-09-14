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

"""Validate the release structure, documentation, notices, and RTL consistency.

This checker is intentionally simulator-independent. It protects repository
properties that are easy to regress during documentation or release work:
English path naming, complete milestone packaging, valid local links, clean
source state, notice consistency, deterministic manifests, and identical
copies of shared RTL. Functional RTL behavior is checked by the simulator
regression and by the independent architectural reference model.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "project_manifest.json"

PROJECT_NOTICE = "Copyright 2026 Jordan Nzokou and Doeg Tiozang"
PROJECT_NAME = "Nexvantis"
PROJECTS = [
    "01_mux",
    "02_pc_and_adders",
    "03_alu",
    "04_register_file",
    "05_immediate_extension",
    "06_memories",
    "07_control_unit",
    "08_alu_register_integration",
    "09_load_store_integration",
    "10_branch_integration",
    "11_final_processor",
]

# These extensions represent human-readable repository assets. Binary diagrams
# and PDFs carry metadata/visible notices but are not decoded by this lightweight
# checker; their metadata is written by the deterministic generators.
TEXT_SUFFIXES = {
    ".asm",
    ".csv",
    ".do",
    ".drawio",
    ".hex",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".svg",
    ".tex",
    ".txt",
    ".v",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "LICENSE",
    "Makefile",
    "NOTICE",
    "VERSION",
}
EXECUTABLE_SUFFIXES = {".asm", ".do", ".hex", ".ps1", ".py", ".sh", ".v"}

GENERATED_DIRECTORY_NAMES = {
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "_minted-report",
    "build",
    "work",
}
GENERATED_FILE_NAMES = {"transcript", "vsim.wlf"}
GENERATED_FILE_SUFFIXES = {
    ".aux",
    ".fdb_latexmk",
    ".fls",
    ".fst",
    ".lof",
    ".log",
    ".lol",
    ".lot",
    ".out",
    ".pyc",
    ".toc",
    ".vcd",
    ".vvp",
    ".wlf",
    ".xdv",
}

REQUIRED_README_HEADINGS = [
    "## Engineering objective",
    "## Design overview",
    "## Interface contract",
    "## Verification strategy",
    "## Files",
    "## Run",
    "## Review focus",
    "## Integration role",
    "## Scope boundary",
]

# French path fragments are rejected because the release is entirely English.
FORBIDDEN_FRENCH_PATH_FRAGMENTS = [
    "additionneurs",
    "banc_de_registres",
    "diagrammes",
    "extension_immediat",
    "integration_branchement",
    "manuel_riscv_monocycle",
    "memoires",
    "outils",
    "processeur_final",
    "unite_de_controle",
]

# A year-qualified copyright line is accepted only when it matches the standard
# Nexvantis project notice. Generic uses of the word "copyright" in Apache-2.0
# remain valid because they are license language rather than owner notices.
YEAR_COPYRIGHT = re.compile(r"Copyright\s+\d{4}[^\r\n]*", re.IGNORECASE)


def read_text(path: Path) -> str | None:
    """Read one UTF-8 text asset, returning None for non-text/binary content."""

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def normalized_rtl(path: Path) -> str:
    """Normalize line endings/trailing spaces before shared-RTL comparison."""

    text = path.read_text(encoding="utf-8")
    return "\n".join(line.rstrip() for line in text.splitlines()).strip() + "\n"


def load_manifest() -> dict[str, dict[str, object]]:
    """Parse and return the ordered milestone mapping from the JSON manifest."""

    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    projects = document.get("projects")
    if not isinstance(projects, dict):
        raise ValueError("manifest is missing the projects object")
    return projects


def file_requires_notice(path: Path) -> bool:
    """Return whether a human-readable file must contain the project notice."""

    return path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES


def iter_markdown_targets(markdown: Path) -> Iterable[str]:
    """Yield local link/image targets from one Markdown document."""

    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    content = markdown.read_text(encoding="utf-8")
    for match in link_pattern.finditer(content):
        raw_target = match.group(1).strip()
        if raw_target.startswith("<") and ">" in raw_target:
            raw_target = raw_target[1 : raw_target.index(">")]
        else:
            # Markdown permits an optional title after a whitespace separator.
            raw_target = raw_target.split()[0]
        yield raw_target


def main() -> int:
    errors: list[str] = []

    # ------------------------------------------------------------------
    # Release-level files and milestone packaging
    # ------------------------------------------------------------------
    required_root_files = [
        "README.md",
        "LICENSE",
        "NOTICE",
        "VERSION",
        "Makefile",
        "project_manifest.json",
        "run_all_linux.sh",
        "run_all_windows.ps1",
        "scripts/build_report.sh",
        "scripts/generate_checksums.py",
        "scripts/generate_diagrams.py",
        "00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf",
        "00_documentation/report_source/nexvantis_rv32i_single_cycle_report.tex",
    ]
    for relative in required_root_files:
        if not (ROOT / relative).is_file():
            errors.append(f"Missing release file: {relative}")

    root_readme = ROOT / "README.md"
    if root_readme.is_file():
        root_text = root_readme.read_text(encoding="utf-8")
        if "## Scripts and automation" not in root_text:
            errors.append("Root README is missing the Scripts and automation section")

    for project in PROJECTS:
        directory = ROOT / project
        if not directory.is_dir():
            errors.append(f"Missing project directory: {project}")
            continue
        for required in ("README.md", "run_questa.do", "run_iverilog.sh"):
            if not (directory / required).is_file():
                errors.append(f"Missing {project}/{required}")

    # ------------------------------------------------------------------
    # Manifest integrity and source references
    # ------------------------------------------------------------------
    try:
        manifest = load_manifest()
    except Exception as exc:  # Validation must aggregate failures for reviewers.
        errors.append(f"Cannot parse project_manifest.json: {exc}")
        manifest = {}

    if list(manifest) != PROJECTS:
        errors.append("Manifest project order/content does not match the milestone list")

    for project, config in manifest.items():
        directory = ROOT / project
        top = config.get("top")
        sources = config.get("sources", [])
        if not top or not isinstance(sources, list) or not sources:
            errors.append(f"Incomplete manifest entry: {project}")
            continue
        for source in sources:
            if not (directory / str(source)).is_file():
                errors.append(f"Manifest references missing file: {project}/{source}")

    # ------------------------------------------------------------------
    # README completeness and local-link integrity
    # ------------------------------------------------------------------
    for project in PROJECTS:
        readme = ROOT / project / "README.md"
        if readme.is_file():
            content = readme.read_text(encoding="utf-8")
            for heading in REQUIRED_README_HEADINGS:
                if heading not in content:
                    errors.append(f"Missing README section in {project}: {heading}")

    for markdown in ROOT.rglob("*.md"):
        for raw_target in iter_markdown_targets(markdown):
            target = urllib.parse.unquote(raw_target.split("#", 1)[0])
            if not target or target.startswith(("data:", "http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(
                    f"Markdown link escapes repository: "
                    f"{markdown.relative_to(ROOT)} -> {raw_target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"Broken Markdown link: {markdown.relative_to(ROOT)} -> {raw_target}"
                )

    # ------------------------------------------------------------------
    # Clean worktree, English paths, ASCII executable sources, and notices
    # ------------------------------------------------------------------
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        relative_lower = relative.as_posix().lower()

        if any(fragment in relative_lower for fragment in FORBIDDEN_FRENCH_PATH_FRAGMENTS):
            errors.append(f"Non-English path remains: {relative}")

        if path.is_dir():
            if path.name in GENERATED_DIRECTORY_NAMES:
                errors.append(f"Generated directory committed: {relative}")
            continue

        if path.name in GENERATED_FILE_NAMES or path.suffix.lower() in GENERATED_FILE_SUFFIXES:
            errors.append(f"Generated artifact committed: {relative}")

        if path.suffix.lower() in EXECUTABLE_SUFFIXES or path.name == "Makefile":
            if any(byte >= 128 for byte in path.read_bytes()):
                errors.append(f"Non-ASCII character in executable source: {relative}")

        text = read_text(path)
        if text is None:
            continue

        if file_requires_notice(path):
            if PROJECT_NOTICE not in text:
                errors.append(f"Missing Nexvantis copyright notice: {relative}")

            for match in YEAR_COPYRIGHT.finditer(text):
                if not match.group(0).strip().startswith(PROJECT_NOTICE):
                    errors.append(
                        f"Unexpected year-qualified copyright notice in {relative}: "
                        f"{match.group(0).strip()}"
                    )

        # Stable diffs and review cleanliness require all committed text lines to
        # be free of trailing spaces. Generated SVG is normalized by its generator.
        for line_number, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line:
                errors.append(f"Trailing whitespace: {relative}:{line_number}")
                break

    # ------------------------------------------------------------------
    # Verilog structure and exact leading notice
    # ------------------------------------------------------------------
    verilog_header = "/**\n * Copyright 2026 Jordan Nzokou and Doeg Tiozang"
    for path in ROOT.rglob("*.v"):
        text = path.read_text(encoding="utf-8")
        module_count = len(re.findall(r"(?m)^\s*module\s+", text))
        endmodule_count = len(re.findall(r"(?m)^\s*endmodule\b", text))
        if module_count != endmodule_count:
            errors.append(
                f"Module balance mismatch in {path.relative_to(ROOT)}: "
                f"module={module_count}, endmodule={endmodule_count}"
            )
        if not text.startswith(verilog_header):
            errors.append(f"Incorrect Verilog copyright header: {path.relative_to(ROOT)}")

    # ------------------------------------------------------------------
    # Shared RTL consistency across independently executable integrations
    # ------------------------------------------------------------------
    repeated_modules = [
        "Mux.v",
        "PC.v",
        "PC_Adder.v",
        "ALU.v",
        "Register_File.v",
        "Sign_Extend.v",
        "Instruction_Memory.v",
        "Data_Memory.v",
        "Main_Decoder.v",
        "ALU_Decoder.v",
        "Control_Unit_Top.v",
        "Single_Cycle_Top.v",
    ]
    integration_directories = [
        ROOT / "08_alu_register_integration",
        ROOT / "09_load_store_integration",
        ROOT / "10_branch_integration",
        ROOT / "11_final_processor",
    ]
    for filename in repeated_modules:
        groups: dict[str, list[str]] = defaultdict(list)
        for directory in integration_directories:
            path = directory / filename
            if path.exists():
                groups[normalized_rtl(path)].append(directory.name)
        if len(groups) > 1:
            summary = "; ".join(",".join(names) for names in groups.values())
            errors.append(f"Repeated RTL diverged for {filename}: {summary}")

    # ------------------------------------------------------------------
    # Diagram-system completeness
    # ------------------------------------------------------------------
    try:
        diagram_manifest = json.loads(
            (ROOT / "13_diagrams" / "diagram_manifest.json").read_text(encoding="utf-8")
        )
        diagrams = diagram_manifest.get("diagrams", [])
        if len(diagrams) != 23:
            errors.append(f"Diagram manifest contains {len(diagrams)} entries; expected 23")
        if diagram_manifest.get("version") != "6.0.0":
            errors.append("Diagram manifest version is not 6.0.0")
        if diagram_manifest.get("canonical_format") != "drawio":
            errors.append("Diagram manifest canonical format is not drawio")
        required_formats = {"drawio", "svg", "png", "pdf"}
        if set(diagram_manifest.get("formats", [])) != required_formats:
            errors.append("Diagram manifest format set is incomplete")
        combined = ROOT / "13_diagrams" / "source" / "Nexvantis_Diagram_Library.drawio"
        if not combined.is_file() or combined.stat().st_size == 0:
            errors.append("Missing combined Draw.io diagram library")
        for entry in diagrams:
            stem = entry.get("stem")
            if not stem:
                errors.append("Diagram manifest contains an entry without a stem")
                continue
            source = ROOT / "13_diagrams" / "source" / f"{stem}.drawio"
            if not source.is_file() or source.stat().st_size == 0:
                errors.append(f"Missing native Draw.io source: {source.relative_to(ROOT)}")
            for directory, suffix in (("svg", ".svg"), ("png", ".png"), ("pdf", ".pdf")):
                output = ROOT / "13_diagrams" / directory / f"{stem}{suffix}"
                if not output.is_file() or output.stat().st_size == 0:
                    errors.append(f"Missing diagram output: {output.relative_to(ROOT)}")
    except Exception as exc:
        errors.append(f"Cannot validate diagram manifest: {exc}")

    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Repository validation passed: {len(PROJECTS)} milestones, "
        f"{len(list(ROOT.rglob('*.v')))} Verilog files, 23 native Draw.io "
        "diagram families, and the Version 6 ISA workbook."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
