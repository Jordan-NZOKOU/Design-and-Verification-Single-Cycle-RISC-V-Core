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
# Validation Status

## Release checks

Version 6 is checked through independent layers:

1. **Repository preflight** - structure, links, English paths, standard project
   notices, README sections, manifest references, generated-artifact hygiene,
   shared RTL consistency, Draw.io completeness, and ISA-workbook presence.
2. **Assembler unit tests** - eight tests covering R/I/S/B encodings, labels,
   negative immediates, alignment, duplicate labels, and invalid registers.
3. **Reference-model tests** - four integration tests for arithmetic,
   load/store, branching, and the final processor program.
4. **Program-image reproduction** - the mini-assembler regenerates the committed
   final ROM image byte-for-byte.
5. **Architectural execution** - the independent model reaches 40 cycles, two
   stores, 27 taken branches, and final `PC = 0x0000003C`.
6. **Diagram generation** - all 23 native Draw.io figures, the combined Draw.io
   library, and synchronized SVG/PNG/PDF exports are regenerated and validated.
7. **ISA workbook verification** - the six-sheet `.xlsx` artifact is inspected
   for instruction data, encoding tables, control vectors, register model,
   memory contract, formulas, and visual layout.
8. **Report build and inspection** - the English XeLaTeX report is rebuilt from
   current repository listings and the Version 6 vector diagrams. The resulting
   **174-page A4 PDF** was rendered page-by-page to PNG; all pages were reviewed
   through complete contact sheets, with targeted full-size checks of key pages.
   No clipping, overlap, missing-glyph block, or major layout defect was found.

The aggregate non-simulator command is:

```bash
make preflight
```

## Repository preflight scope

`make preflight` validates:

- the eleven milestone directories and manifest order;
- required README sections and local Markdown links;
- English path names;
- project-notice presence and year-qualified copyright consistency;
- structural Verilog module/endmodule balance;
- consistency of repeated integration RTL;
- absence of committed simulator/report build artifacts;
- presence of the Version 6 PDF report and Excel ISA workbook;
- presence and validity of all native Draw.io sources and exports;
- mini-assembler and reference-model tests;
- final HEX-image reproducibility;
- expected final architectural state in the independent model.

## Diagram validation

`python3 scripts/generate_diagrams.py --validate-only` requires 23 native
`.drawio` sources, the combined multi-page Draw.io library, and every SVG, PNG,
and PDF export. It checks the manifest contract, XML structure, notice text, and
non-empty release outputs.

## ISA workbook validation

`Nexvantis_RV32I_Instruction_Set_Architecture_V6.xlsx` contains six structured
worksheets: ISA Overview, Instruction Set, Encoding Formats, Control Matrix,
Register Model, and Memory & Execution. The release check confirms that the
workbook archive is valid and that the documented encodings match the control
and execution RTL.

## RTL simulation status

The repository contains complete QuestaSim/ModelSim and Icarus Verilog flows,
including per-milestone scripts and GitHub Actions. These simulators were not
installed in the release-generation environment, so no local RTL-simulator run
is claimed here. Static repository checks, assembler tests, reference-model
integration tests, program-image reproduction, diagram validation, workbook
inspection, and full PDF rendering were executed successfully.

## Functional expectations

The final reference-model state is documented in `docs/RESULTS.md`. A release is
not considered valid if the program image, model, RTL checker, ISA workbook, and
documentation disagree.
