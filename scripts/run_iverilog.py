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

"""Compile and run one or more Nexvantis milestones with Icarus Verilog.

The manifest is the single source of truth for project order, top-level names,
source ordering, and expected VCD filenames. Keeping this logic in one driver
prevents project-local scripts and CI from drifting apart.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "project_manifest.json"


def load_manifest() -> dict[str, dict[str, Any]]:
    """Load and return only the ordered project mapping from the JSON manifest."""
    document = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    projects = document.get("projects")
    if not isinstance(projects, dict):
        raise RuntimeError("project_manifest.json does not contain a projects object")
    return projects


def require_tool(name: str) -> str:
    """Resolve a simulator executable or fail with an actionable message."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(
            f"Required executable '{name}' was not found in PATH. "
            "Install Icarus Verilog before running this command."
        )
    return executable


def run_project(
    project_name: str,
    config: dict[str, Any],
    *,
    dump_vcd: bool,
    keep_build: bool,
) -> None:
    """Compile and execute one self-contained milestone.

    A private build directory prevents compiled output from mixing with source
    files. Unless requested otherwise, it is deleted after a successful run.
    """
    iverilog = require_tool("iverilog")
    vvp = require_tool("vvp")

    project_dir = ROOT / project_name
    build_dir = project_dir / "build"
    output = build_dir / "simv"

    if build_dir.exists() and not keep_build:
        shutil.rmtree(build_dir)
    build_dir.mkdir(exist_ok=True)

    # -g2012 accepts the Verilog/SystemVerilog constructs used by the testbenches.
    # -Wall and -Wimplicit make common integration mistakes visible in CI logs.
    command = [
        iverilog,
        "-g2012",
        "-Wall",
        "-Wimplicit",
        "-s",
        str(config["top"]),
        "-o",
        str(output),
    ]
    if dump_vcd:
        command.append("-DDUMP_VCD")
    command.extend(str(project_dir / source) for source in config["sources"])

    print(f"===== {project_name} =====", flush=True)
    subprocess.run(command, cwd=project_dir, check=True)
    subprocess.run([vvp, str(output)], cwd=project_dir, check=True)

    if not keep_build:
        shutil.rmtree(build_dir)


def parse_args() -> argparse.Namespace:
    """Define the command-line interface used by Make and project wrappers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Run only the named project. Repeat to select multiple projects.",
    )
    parser.add_argument(
        "--vcd",
        action="store_true",
        help="Enable DUMP_VCD and retain the generated waveform file.",
    )
    parser.add_argument(
        "--keep-build",
        action="store_true",
        help="Keep per-project compiled build directories after simulation.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available project names and exit.",
    )
    return parser.parse_args()


def main() -> int:
    """Validate selection, run projects in order, and propagate failures."""
    args = parse_args()
    manifest = load_manifest()

    if args.list:
        print("\n".join(manifest))
        return 0

    selected = args.project or list(manifest)
    unknown = [name for name in selected if name not in manifest]
    if unknown:
        print(f"Unknown project(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    try:
        for name in selected:
            run_project(
                name,
                manifest[name],
                dump_vcd=args.vcd,
                keep_build=args.keep_build,
            )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Regression failed: {exc}", file=sys.stderr)
        return 1

    print("All selected Icarus Verilog regressions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
