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

# Milestone 05 - Immediate Reconstruction and Sign Extension

<p align="center">
  <img src="../13_diagrams/svg/13_immediate_reconstruction.svg" alt="Milestone 05 - Immediate Reconstruction and Sign Extension diagram" width="100%">
</p>

## Engineering objective

Reconstruct non-uniform RISC-V immediate fields and convert them into correctly signed 32-bit operands and PC-relative offsets.

## Design overview

`Sign_Extend` supports I-, S-, and B-type formats. I-type bits are contiguous, S-type bits are split around register fields, and B-type bits are both split and reordered. B-type bit 0 is inserted as zero because the encoded branch displacement is aligned to two-byte units.

### Architectural contract

Concatenations reproduce the ISA bit placement exactly. Replication operators copy `In[31]` into the upper result bits. A complete combinational `case` returns zero for unsupported selectors, preventing stale values or latch inference.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `In[31:0]` | input | Complete instruction word |
| `ImmSrc[1:0]` | input | `00`=I, `01`=S, `10`=B |
| `Imm_Ext[31:0]` | output | Reconstructed sign-extended immediate |

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

- Positive and negative I-type immediates.
- Positive and negative S-type offsets.
- Positive and negative B-type branch displacements.
- Unsupported `ImmSrc` returns zero.
- Use known machine words so the test also documents field placement.

### Signals to inspect in GTKWave

`instr`, `imm_src`, `imm_ext`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `Sign_Extend.v` | I/S/B decoder and sign extender. |
| `Sign_Extend_tb.v` | Seven directed reconstruction cases. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 05_immediate_extension
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
make test-project PROJECT=05_immediate_extension
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

The B-type concatenation deserves line-by-line review. Confirm ordering `imm[12|11|10:5|4:1|0]` and that negative cases replicate the sign bit.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

The result supplies ALU operand B for immediate/address instructions and the branch-target adder for BEQ.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

U- and J-type immediates, compressed instructions, and zero-extended CSR immediates are outside the implemented subset.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
