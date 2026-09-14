<!--
/**
 * Copyright 2026 Jordan Nzokou and Doeg Tiozang
 * Project: Nexvantis
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
-->

# GitHub Publishing Checklist

## Repository preparation

- [ ] Choose a concise repository name, for example `nexvantis-rv32i-single-cycle`.
- [ ] Keep the default branch clean and remove local simulator artifacts.
- [ ] Run `make preflight`.
- [ ] Run `make test` on a machine with Icarus Verilog.
- [ ] Run the Questa regression when a licensed installation is available.
- [ ] Rebuild diagrams and the report with `make diagrams` and `make report`.
- [ ] Regenerate checksums with `python3 scripts/generate_checksums.py`.
- [ ] Confirm `git status` contains only intended release changes.

## GitHub presentation

- [ ] Add a repository description mentioning Verilog, RV32I, and verification.
- [ ] Add topics: `risc-v`, `rv32i`, `verilog`, `rtl`, `cpu`, `verification`, `questasim`, `icarus-verilog`.
- [ ] Ensure the root architecture SVG renders correctly and the native Draw.io source opens cleanly.
- [ ] Pin the final report, ISA workbook, Draw.io library, or release ZIP in the GitHub release.
- [ ] Enable GitHub Actions and verify the workflow is green.
- [ ] Keep issue and pull-request templates enabled.

## Release checks

- [ ] Run `make preflight` and resolve every notice-consistency finding.
- [ ] Confirm every text source contains the Nexvantis notice.
- [ ] Confirm all paths and visible diagram labels are English.
- [ ] Confirm no `.vcd`, `.vvp`, `work/`, `build/`, LaTeX auxiliary file, or Python cache is committed.
- [ ] Confirm documentation links resolve from a clean clone.
- [ ] Publish the SHA-256 inventory with the release artifacts.

## Suggested release description

State the supported ISA subset, simulator paths, final architectural evidence,
known scope limits, and the fact that the diagrams/report are reproducible. Do
not claim full RV32I compliance or production readiness.
