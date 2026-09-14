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

# Milestone 11 - Complete Processor and Architectural Regression

<p align="center">
  <img src="../13_diagrams/svg/21_final_datapath.svg" alt="Milestone 11 - Complete Processor and Architectural Regression diagram" width="100%">
</p>

## Engineering objective

Run the complete supported instruction subset in one program and verify architectural state, memory effects, control-flow evidence, and terminal behavior.

## Design overview

The final program combines immediate and register ALU operations, two stores, one load, a taken forward BEQ, a negative immediate, signed comparison, and a terminal self-branch. The testbench observes both end-state and execution trajectory so a coincidentally correct final value cannot hide a control-flow defect.

### Architectural contract

All blocks remain structural and combinational/sequential boundaries are unchanged. Debug outputs are observation-only. The `MEMFILE` parameter makes the ROM image explicit and allows a testbench to select the local program without hard-coding a global path.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `clk`, `rst_n` | inputs | Processor state control |
| `PC_Debug[31:0]` | output | Current PC for trajectory checks |
| `Instr_Debug[31:0]` | output | Current instruction |
| `MemWrite_Debug` | output | Store-count evidence |
| `ALUResult_Debug[31:0]` | output | Current ALU/address result |
| `WriteData_Debug[31:0]` | output | Current store data |
| `Result_Debug[31:0]` | output | Current register write-back data |

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

- Check eleven registers `x5` through `x15` against known values.
- Check data-memory words 0 and 1.
- Require exactly two store pulses.
- Fail if the instruction at `PC=0x24` executes.
- Require taken-branch evidence.
- Require stabilization in the terminal loop at `PC=0x3C`.
- Cross-check the same image with the independent Python model.
- Reproduce `program.hex` from `program.asm` with the mini-assembler.

### Signals to inspect in GTKWave

`PC_Debug`, `Instr_Debug`, `RegWrite`, `ALUControl`, `ALUResult_Debug`, `MemWrite_Debug`, `WriteData_Debug`, `Result_Debug`, registers `x5..x15`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `Single_Cycle_Top.v` | Complete structural processor. |
| `Single_Cycle_Top_tb.v` | Final self-checking architectural regression. |
| `program.asm` / `program.hex` | Source program and committed ROM image. |
| `trace_reference.csv` | Cycle-oriented expected trace reference. |
| Core `*.v` files | Local, consistency-checked module copies. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 11_final_processor
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
make test-project PROJECT=11_final_processor
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Review the processor by instruction class, then compare hardware evidence with the reference model. Confirm debug ports do not feed back into the design and that the final checker cannot pass with X/Z values.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

This is the release-level RTL target used by the complete regression, report, portfolio documentation, and future extension roadmap.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

The acceptance claim is limited to the documented twelve-instruction subset and behavioral memory environment.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
