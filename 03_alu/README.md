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

# Milestone 03 - 32-bit Arithmetic and Logic Unit

<p align="center">
  <img src="../13_diagrams/svg/08_alu_architecture.svg" alt="Milestone 03 - 32-bit Arithmetic and Logic Unit diagram" width="100%">
</p>

## Engineering objective

Implement the execution primitive for arithmetic, logic, address generation, signed comparison, and BEQ equality evaluation, with deterministic status flags.

## Design overview

The combinational ALU supports ADD, SUB, AND, OR, and signed SLT. Arithmetic uses a 33-bit expression so unsigned carry/no-borrow is retained. Signed overflow is calculated separately from carry. `Zero` and `Negative` are derived continuously from the selected result.

### Architectural contract

Default assignments precede the `case` statement so every procedural output is driven for every input combination. ADD and SUB explicitly extend operands to 33 bits. SLT casts both operands with `$signed`, avoiding incorrect unsigned ordering around the sign boundary. Unsupported controls return zero and clear arithmetic flags.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `A[31:0]`, `B[31:0]` | inputs | ALU operands |
| `ALUControl[2:0]` | input | Internal operation encoding |
| `Result[31:0]` | output | Selected arithmetic/logic result |
| `Carry` | output | ADD carry-out or SUB no-borrow indication |
| `OverFlow` | output | Signed arithmetic overflow |
| `Zero` | output | Asserted when all result bits are zero |
| `Negative` | output | Copy of result sign bit |

### Timing model

Combinational outputs settle after input changes according to simulator delta
cycles. Any architectural write occurs only on the rising edge defined by the
module contract. `rst_n` is active-low and synchronous wherever state is reset.
The milestone does not introduce hidden state beyond the documented registers or
memory array.

## Verification strategy

The testbench is directed, self-checking, and CI-friendly. It initializes every
stimulus signal, uses reusable check tasks, compares with `!==` to reject unknown
values, accumulates mismatches, optionally writes a VCD when `DUMP_VCD` is
defined, and ends with one unambiguous verdict.

- Nominal addition and subtraction.
- Unsigned carry on `0xFFFFFFFF + 1`.
- Positive-to-negative signed ADD overflow.
- Negative-to-positive signed SUB overflow.
- Bitwise AND and OR masks.
- Signed SLT for `-1 < 1` and false `5 < 4`.
- Zero/Negative derivation and unsupported-control default behavior.

### Signals to inspect in GTKWave

`A`, `B`, `ALUControl`, `Result`, `Carry`, `OverFlow`, `Zero`, `Negative`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `ALU.v` | Combinational ALU and flag logic. |
| `ALU_tb.v` | Eleven directed vectors through a reusable transaction task. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 03_alu
vsim -c -do run_questa.do
```

The script recreates the work library, compiles sources in dependency order,
runs the testbench to completion, and writes the milestone VCD.

### Icarus Verilog

From the milestone directory:

```bash
./run_iverilog.sh
```

From the repository root:

```bash
make test-project PROJECT=03_alu
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Distinguish carry from signed overflow, inspect the subtraction carry semantics, and confirm that signed comparison is independent of an overflow-prone subtract-and-sign shortcut.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

The ALU performs register arithmetic, immediate arithmetic, load/store address generation, and BEQ comparison.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

Shift operations, multiplication, division, unsigned SLT, saturation, and exception signaling are not implemented.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
