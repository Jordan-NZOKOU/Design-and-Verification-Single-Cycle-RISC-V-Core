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

# Milestone 10 - BEQ and Next-PC Integration

<p align="center">
  <img src="../13_diagrams/svg/20_branch_path.svg" alt="Milestone 10 - BEQ and Next-PC Integration diagram" width="100%">
</p>

## Engineering objective

Prove that equality comparison, B-type immediate reconstruction, target calculation, branch qualification, and next-PC selection work together.

## Design overview

The program creates an equal comparison, takes a BEQ, skips an instruction, stores a branch-target value, and enters a terminal self-branch. The test does not rely only on the final register value: it also records the PC trajectory, branch count, store count, and terminal PC.

### Architectural contract

BEQ reads both registers, forces ALU SUB, and derives equality from `Zero`. The B-type immediate already contains the implicit low zero, so `PC + ImmExt` produces the byte target directly. The next-PC mux selects the target only when `Branch & Zero & funct3==000`.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `PC_Debug` | output | Evidence of skipped and terminal addresses |
| `Instr_Debug` | output | Current branch or target instruction |
| `ALUResult_Debug` | output | Subtraction result used by Zero |
| `MemWrite_Debug` | output | One expected store |
| Internal `PCSrc` | waveform signal | Qualified branch decision |

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

- Check `x1=1`, `x2=1`, and target-side-effect register `x3=7`.
- Check `mem[0]=7` and exactly one store pulse.
- Fail if skipped `PC=12` is ever observed.
- Require at least two taken-branch events.
- Require final PC stability at decimal 24 (`0x18`).

### Signals to inspect in GTKWave

`PC_Debug`, `Instr_Debug`, `PCSrc`, `Zero`, `ImmExt`, `PCTarget`, `PCNext`, `MemWrite_Debug`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `program.asm` / `program.hex` | Branch-directed workload. |
| `Integration_Branch_tb.v` | PC-path, state, count, and terminal-loop checker. |
| `Single_Cycle_Top.v` + core RTL | Local integration copy. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 10_branch_integration
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
make test-project PROJECT=10_branch_integration
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Confirm branch target base is the current PC, not PC+4; inspect B-immediate bit ordering; and verify unsupported branch function codes cannot redirect control flow.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

This milestone adds the final functional path required by the complete regression.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

Only BEQ is supported. There is no prediction, delay slot, branch-link register, or jump path.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
