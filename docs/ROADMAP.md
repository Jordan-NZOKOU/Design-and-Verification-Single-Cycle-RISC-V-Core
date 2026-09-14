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

# Technical Roadmap

The current release is intentionally frozen to the verified single-cycle subset.
The following extensions are ordered to preserve reviewability.

## Phase 1 - Verification depth

- add SystemVerilog assertions for x0, legal write controls, and PC alignment;
- add a scoreboard fed by an instruction-level reference transaction stream;
- collect functional coverage for opcode/function combinations;
- add lint and synthesis checks to CI when tools are available;
- introduce formal properties for primitive blocks and branch behavior.

## Phase 2 - RV32I coverage

- shifts (`SLL`, `SRL`, `SRA` and immediate forms);
- unsigned comparison (`SLTU`, `SLTIU`);
- `LUI` and `AUIPC`;
- `JAL` and `JALR`;
- byte/halfword loads and stores with byte enables;
- explicit illegal-instruction and misalignment handling.

## Phase 3 - Implementation realism

- replace behavioral memories with target wrappers;
- add a ready/valid memory interface;
- parameterize memory depth and reset vector;
- synthesize for an FPGA target and report area/timing;
- add constraints and implementation scripts.

## Phase 4 - Pipelined core

- split into IF/ID/EX/MEM/WB stages;
- add pipeline registers and valid control;
- implement forwarding and load-use stalls;
- flush on taken control transfer;
- add branch prediction only after the baseline pipeline is verified.

No roadmap item is claimed as implemented in the current repository.
