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

# Run the complete QuestaSim/ModelSim regression on Linux or macOS.
#
# Each milestone remains self-contained and owns its compile order, top-level
# testbench, waveform setup, and final verdict through run_questa.do. This root
# script only establishes the release order and propagates the first failure.
set -euo pipefail

# Resolve the repository independently of the caller's current directory.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The order mirrors project_manifest.json and the architectural progression in
# the report. A failure stops the loop immediately because set -e is active.
PROJECTS=(
    01_mux
    02_pc_and_adders
    03_alu
    04_register_file
    05_immediate_extension
    06_memories
    07_control_unit
    08_alu_register_integration
    09_load_store_integration
    10_branch_integration
    11_final_processor
)

# Check the proprietary simulator once before entering the loop. Exit status 127
# follows the conventional shell meaning for a missing executable.
if ! command -v vsim >/dev/null 2>&1; then
    echo "Error: 'vsim' was not found in PATH." >&2
    echo "Install QuestaSim/ModelSim or use 'make iverilog' instead." >&2
    exit 127
fi

for project in "${PROJECTS[@]}"; do
    echo "===== ${project} ====="

    # A subshell contains the directory change so the next milestone always
    # starts from a known repository-root context.
    (
        cd "${ROOT_DIR}/${project}"
        vsim -c -do run_questa.do
    )
done

echo "All QuestaSim/ModelSim regressions passed."
