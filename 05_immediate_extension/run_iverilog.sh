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

# Project-local Icarus Verilog wrapper for: Immediate Reconstruction and Sign Extension
#
# The central Python runner owns source ordering and error handling. This wrapper
# selects only the current milestone, enables waveform generation, and retains
# the compiled build directory so a reviewer can inspect or rerun the executable.
set -euo pipefail

# Resolve the repository root from the wrapper location. The command therefore
# behaves identically when invoked from this directory or through another shell.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

python3 "${ROOT_DIR}/scripts/run_iverilog.py" \
    --project "05_immediate_extension" \
    --vcd \
    --keep-build
