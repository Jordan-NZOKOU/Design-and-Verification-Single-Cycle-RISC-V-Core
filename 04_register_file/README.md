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

# Milestone 04 - RV32I Register File

<p align="center">
  <img src="../13_diagrams/svg/10_register_file_architecture.svg" alt="Milestone 04 - RV32I Register File diagram" width="100%">
</p>

## Engineering objective

Implement the architectural integer-register state with two combinational read ports, one clocked write port, and explicit protection of the RISC-V zero register.

## Design overview

The block stores 32 words of 32 bits. Five-bit addresses select `x0` through `x31`. Writes occur at a rising edge only when `WE3=1` and `A3!=0`; reads are asynchronous. Both read ports bypass stored array contents when their address is zero, guaranteeing `x0==0`.

### Architectural contract

A full-array synchronous reset is retained for deterministic simulation and straightforward waveform review. This choice is explicit because some FPGA/ASIC flows would use initialization or different structures for efficient memory inference. Nonblocking assignments model all state updates.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `clk`, `rst_n` | inputs | Synchronous state control |
| `WE3` | input | Write enable |
| `A1`, `A2` | inputs | Five-bit asynchronous read addresses |
| `A3` | input | Five-bit synchronous write address |
| `WD3[31:0]` | input | Write data |
| `RD1`, `RD2` | outputs | Independent asynchronous read data |

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

- Check reset clears representative registers.
- Write and read `x5`.
- Write `x6` and prove independent simultaneous read ports.
- Disable `WE3` and prove the previous value is retained.
- Attempt a write to `x0` and prove the architectural invariant.
- Reassert reset and confirm both written registers clear.

### Signals to inspect in GTKWave

`clk`, `rst_n`, `WE3`, `A1`, `A2`, `A3`, `WD3`, `RD1`, `RD2`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `Register_File.v` | Register array, synchronous write/reset, x0 read bypass. |
| `Register_File_tb.v` | Clocked self-checking sequence and hierarchical state checks. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 04_register_file
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
make test-project PROJECT=04_register_file
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Review the x0 guard on both write and read paths, the asynchronous read semantics, and the technology implications of clearing all 32 words in one reset loop.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

Instruction fields `rs1`, `rs2`, and `rd` connect directly to the three addresses. The result mux drives `WD3` and `RegWrite` drives `WE3`.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

No bypass/forwarding, multiple write ports, ECC/parity, privilege banking, or debug write port is provided.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
