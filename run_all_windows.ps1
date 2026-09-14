<#
Copyright 2026 Jordan Nzokou and Doeg Tiozang
Project: Nexvantis

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
#>

<#
Run the complete QuestaSim/ModelSim regression from Windows PowerShell.

Each milestone's run_questa.do file owns compilation, simulation, VCD export,
and the self-checking testbench verdict. This wrapper preserves the documented
milestone order and converts any non-zero simulator status into a PowerShell
exception suitable for local automation or CI.
#>

# Convert command and native-process failures into terminating errors.
$ErrorActionPreference = "Stop"

# Resolve paths from the script location so the command may be launched from any
# working directory without changing relative source lookup inside milestones.
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Keep this list aligned with project_manifest.json and run_all_linux.sh.
$Projects = @(
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
    "11_final_processor"
)

# Fail before changing directories when the simulator installation is missing.
if (-not (Get-Command vsim -ErrorAction SilentlyContinue)) {
    throw "The 'vsim' executable was not found in PATH. Install QuestaSim/ModelSim or use the Icarus flow."
}

foreach ($Project in $Projects) {
    Write-Host "===== $Project ====="

    # Push/Pop-Location is enclosed in try/finally so a simulator failure cannot
    # leave the caller in a milestone directory.
    Push-Location (Join-Path $Root $Project)
    try {
        & vsim -c -do run_questa.do
        if ($LASTEXITCODE -ne 0) {
            throw "Simulation failed: $Project (exit code $LASTEXITCODE)"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host "All QuestaSim/ModelSim regressions passed."
