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

# Milestone 07 - Main Decoder, ALU Decoder, and Branch Control

<p align="center">
  <img src="../13_diagrams/svg/16_control_unit_hierarchy.svg" alt="Milestone 07 - Main Decoder, ALU Decoder, and Branch Control diagram" width="100%">
</p>

## Engineering objective

Translate RV32I instruction fields into deterministic datapath controls while separating instruction-class decisions from ALU-operation decisions.

## Design overview

`Main_Decoder` maps the opcode to register, immediate, memory, result, branch, and coarse ALU controls. `ALU_Decoder` resolves the exact operation from `ALUOp`, `funct3`, `funct7`, and the opcode. `Control_Unit_Top` composes both and qualifies `PCSrc` for supported BEQ only.

### Architectural contract

Unsupported opcodes default to all write enables deasserted. Address-generation classes force ADD; BEQ forces SUB; ALU instruction classes request function-field decoding. The R-type opcode qualification prevents an I-type immediate bit from being misinterpreted as a SUB `funct7` bit.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `Op[6:0]` | input | Instruction opcode |
| `funct3[2:0]`, `funct7[6:0]` | inputs | Operation subfields |
| `Zero` | input | ALU equality result |
| `RegWrite` | output | Enable architectural register write |
| `ImmSrc[1:0]` | output | Select I/S/B immediate format |
| `ALUSrc` | output | Select RD2 or immediate for ALU B |
| `MemWrite` | output | Enable data-memory store |
| `ResultSrc` | output | Select ALU or memory write-back |
| `PCSrc` | output | Select branch target |
| `ALUControl[2:0]` | output | Select ALU operation |

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

- Decode LW and SW controls.
- Decode all supported R-type ALU operations.
- Decode all supported I-type ALU operations.
- Check BEQ both taken and not taken.
- Suppress a non-BEQ branch `funct3`.
- Check an unsupported opcode produces no architectural write side effect.

### Signals to inspect in GTKWave

`Op`, `funct3`, `funct7`, `Zero`, `RegWrite`, `ImmSrc`, `ALUSrc`, `MemWrite`, `ResultSrc`, `PCSrc`, `ALUControl`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `Main_Decoder.v` | Opcode-class decoder. |
| `ALU_Decoder.v` | Function-level ALU decoder. |
| `Control_Unit_Top.v` | Composition and BEQ qualification. |
| `Control_Unit_Top_tb.v` | Fifteen-vector control matrix. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 07_control_unit
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
make test-project PROJECT=07_control_unit
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Focus on safe defaults, ADD/SUB qualification, BEQ-only PC redirection, and whether every output is assigned in every combinational path.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

This block drives all mux selects, write enables, immediate format selection, ALU operation, and the branch decision in the final datapath.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

No illegal-instruction exception, jump decode, CSR control, memory-size control, privilege state, or microcoded sequencing is implemented.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
