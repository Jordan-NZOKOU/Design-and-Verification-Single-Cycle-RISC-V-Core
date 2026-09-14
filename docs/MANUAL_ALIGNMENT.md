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
# Report and Repository Alignment

The Version 6 PDF is fully English and uses the same directory names, signal
names, script names, Draw.io figure identifiers, instruction encodings, and
acceptance criteria as the GitHub repository and Excel ISA workbook.

| Report topic | Repository location |
|---|---|
| Verilog/RISC-V foundations | Chapters 2-3 of the report |
| Simulation flow | Chapter 4, root Scripts section, per-project scripts |
| Source audit and corrections | Report Part II and design decisions |
| Unit milestones | `01_mux` through `07_control_unit` |
| Integration milestones | `08_alu_register_integration` through `11_final_processor` |
| Verification method | `docs/VERIFICATION_STRATEGY.md` and testbenches |
| Mini-assembler/reference model | `12_tools` and `scripts` |
| Instruction-set architecture workbook | `00_documentation/Nexvantis_RV32I_Instruction_Set_Architecture_V6.xlsx` |
| Draw.io diagrams | `13_diagrams/source`, exports, and `scripts/generate_diagrams.py` |
| Final results | `docs/RESULTS.md` and final testbench |

The report imports the English commented source directly from the repository,
which prevents a separate stale code transcription. Diagram PDFs, GitHub SVGs,
PNG previews, and native Draw.io documents are generated from one shared
geometry model.
