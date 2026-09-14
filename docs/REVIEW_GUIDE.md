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

# Senior Review Guide

## Repository-level questions

- Can a clean clone reproduce validation from documented commands?
- Does every milestone state a bounded engineering claim?
- Are repeated RTL copies checked for divergence?
- Do scripts fail with non-zero status when a test fails?
- Is the final ROM image reproducible from readable assembly?

## RTL questions

### Sequential logic

- Is reset polarity and synchronization unambiguous?
- Are all state updates nonblocking?
- Is state confined to intended modules?

### Combinational logic

- Are all outputs assigned for all control combinations?
- Are signed and unsigned operations explicit?
- Can unsupported inputs create write side effects?
- Are address units (bytes versus words) consistent?

### ISA mapping

- Are `rs1`, `rs2`, and `rd` extracted from the correct fields?
- Are S/B immediate fragments ordered correctly?
- Is SUB qualified by R-type opcode as well as function bits?
- Is BEQ target based on current PC?

## Verification questions

- Does the checker use four-state comparisons?
- Do corner cases distinguish carry from overflow?
- Is x0 protected on both read and write paths?
- Are memory transaction counts checked?
- Does branch testing inspect the PC trajectory, not only final state?
- Is the reference model independent of RTL internals?

## Suggested files

1. `03_alu/ALU.v` and `ALU_tb.v`;
2. `05_immediate_extension/Sign_Extend.v`;
3. `07_control_unit/*.v` and testbench;
4. `11_final_processor/Single_Cycle_Top.v`;
5. `11_final_processor/Single_Cycle_Top_tb.v`;
6. `scripts/reference_model.py`;
7. `scripts/repository_check.py`;
8. `12_tools/mini_assembler.py`.

## Expected discussion topics

A strong project explanation should cover why this architecture is easy to
reason about but slow, how to move toward a pipelined design, what assertions or
formal properties would be added, and how behavioral memories would be replaced
for a target FPGA or ASIC flow.
