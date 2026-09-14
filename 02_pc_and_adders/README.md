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

# Milestone 02 - Program Counter and Address Adders

<p align="center">
  <img src="../13_diagrams/svg/06_pc_update_path.svg" alt="Milestone 02 - Program Counter and Address Adders diagram" width="100%">
</p>

## Engineering objective

Establish the first sequential state element and the combinational address arithmetic required for sequential execution and PC-relative branches.

## Design overview

`PC_Module` stores the current 32-bit program counter. `rst_n` is active-low and synchronous, so reset is sampled only on a rising clock edge. `PC_Adder` is a stateless 32-bit adder used for both `PC+4` and `PC+ImmExt`. The separation between register and adder makes the cycle boundary explicit.

### Architectural contract

The PC uses a nonblocking assignment in an `always @(posedge clk)` block. The adder uses a continuous assignment and intentionally discards carry-out because this subset does not implement address-overflow exceptions. Fixed 32-bit instructions advance by four byte addresses.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `clk` | input | Rising-edge state-update clock |
| `rst_n` | input | Synchronous active-low reset |
| `PC_Next[31:0]` | input | Address captured when reset is inactive |
| `PC[31:0]` | output | Current architectural program counter |
| `a`, `b` | adder inputs | Two 32-bit operands |
| `c` | adder output | 32-bit modulo-2^32 sum |

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

- Assert reset across a rising edge and check `PC=0`.
- Release reset and verify the sequence 0, 4, 8, and 12.
- Reassert reset between edges and prove that PC changes only at the next rising edge.
- Exercise the adder as the source of `PC_Next` rather than forcing values directly.

### Signals to inspect in GTKWave

`clk`, `rst_n`, `pc`, `pc_plus_4`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `PC.v` | Synchronous PC register. |
| `PC_Adder.v` | Combinational 32-bit adder. |
| `PC_tb.v` | Clock/reset generation and self-checking PC sequence. |
| `run_questa.do` / `run_iverilog.sh` | Simulator entry points. |

## Run

### QuestaSim or ModelSim

```bash
cd 02_pc_and_adders
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
make test-project PROJECT=02_pc_and_adders
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Check reset polarity and synchronization carefully. Verify that state uses nonblocking assignment and that the adder contains no procedural storage.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

The final processor instantiates one PC register and two adders: one for the sequential address and one for the branch target.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

No enable, stall, exception vector, alignment trap, or reset vector parameter is implemented.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
