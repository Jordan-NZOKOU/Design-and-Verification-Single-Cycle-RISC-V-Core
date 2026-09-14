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

# Milestone 09 - Load/Store Datapath Integration

<p align="center">
  <img src="../13_diagrams/svg/19_load_store_paths.svg" alt="Milestone 09 - Load/Store Datapath Integration diagram" width="100%">
</p>

## Engineering objective

Validate address generation, synchronous stores, asynchronous loads, memory-to-register write-back, and transaction counting.

## Design overview

The program writes 42 to memory word 0, loads it into another register, computes 84, and stores that result to word 1. This creates end-to-end evidence for both directions of the processor-memory interface.

### Architectural contract

LW and SW both use ALU ADD for `base + sign-extended offset`. SW writes `RD2` at a rising edge when `MemWrite` is high. LW receives combinational `ReadData`, selects it through the result mux, and commits it to `rd` on the next rising edge.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `ALUResult_Debug` | output | Effective byte address for memory instructions |
| `WriteData_Debug` | output | Store value from `rs2` |
| `MemWrite_Debug` | output | Store transaction qualifier |
| `Result_Debug` | output | Load data selected for register write-back |
| Remaining debug ports | outputs | Instruction and PC context |

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

- Check final registers `x5=42`, `x6=42`, and `x7=84`.
- Check `mem[0]=42` and `mem[1]=84`.
- Count exactly two store-enable pulses.
- Observe effective byte addresses and write data in the waveform.

### Signals to inspect in GTKWave

`PC_Debug`, `Instr_Debug`, `ALUResult_Debug`, `WriteData_Debug`, `MemWrite_Debug`, `ReadData`, `Result_Debug`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `program.asm` / `program.hex` | Deterministic load/store sequence. |
| `Integration_Load_Store_tb.v` | Register, memory, and store-count checker. |
| `Single_Cycle_Top.v` + core RTL | Local integration copy. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 09_load_store_integration
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
make test-project PROJECT=09_load_store_integration
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Verify that S-type fields reconstruct the correct offset, that stores use unmodified RD2 as write data, and that the load result rather than the address is written to `rd`.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

This milestone completes the memory and write-back paths used unchanged by the final processor.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

Only aligned 32-bit words and zero-latency reads are supported; there is no bus backpressure or access fault handling.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
