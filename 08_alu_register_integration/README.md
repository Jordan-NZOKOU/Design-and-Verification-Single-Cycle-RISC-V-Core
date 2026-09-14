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

# Milestone 08 - Arithmetic Datapath Integration

<p align="center">
  <img src="../13_diagrams/svg/18_arithmetic_integration.svg" alt="Milestone 08 - Arithmetic Datapath Integration diagram" width="100%">
</p>

## Engineering objective

Integrate fetch, decode, register reads, immediate selection, ALU execution, and register write-back before enabling memory or branch side effects.

## Design overview

This milestone instantiates the complete structural top but executes an arithmetic-only program. It proves that instruction fields reach the correct register addresses, the control unit selects the correct ALU operation and operand source, and results commit to the expected destinations across multiple cycles.

### Architectural contract

The top is structural: it wires previously verified modules rather than reimplementing their behavior. Local copies make the milestone independently compilable. The program exercises immediate setup followed by OR, AND, SUB, and signed SLT operations.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `clk`, `rst_n` | inputs | Processor state control |
| `PC_Debug` | output | Current instruction byte address |
| `Instr_Debug` | output | Fetched instruction |
| `MemWrite_Debug` | output | Must remain low for this program |
| `ALUResult_Debug` | output | Current execute-stage result |
| `WriteData_Debug` | output | Current register-file RD2 value |
| `Result_Debug` | output | Current write-back value |

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

- Run enough cycles to retire the arithmetic program.
- Check `x5=5`, `x6=4`, `x7=5`, `x8=4`, `x9=1`, and `x10=1`.
- Count `MemWrite_Debug` pulses and require exactly zero.
- Use hierarchical register checks only at the architectural end-state.

### Signals to inspect in GTKWave

`PC_Debug`, `Instr_Debug`, `ALUResult_Debug`, `Result_Debug`, `RegWrite`, `ALUControl`, registers `x5..x10`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `Single_Cycle_Top.v` | Structural processor integration. |
| `program.asm` / `program.hex` | Arithmetic workload and ROM image. |
| `Integration_ALU_tb.v` | Architectural end-state checker. |
| Core `*.v` files | Local, consistency-checked module copies. |
| `run_questa.do` / `run_iverilog.sh` | Simulator automation. |

## Run

### QuestaSim or ModelSim

```bash
cd 08_alu_register_integration
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
make test-project PROJECT=08_alu_register_integration
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Trace one R-type and one I-type instruction from machine word to field extraction, control signals, operands, ALU result, and destination write edge.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

This is the baseline processor datapath. Milestone 9 enables meaningful data-memory effects, while milestone 10 validates next-PC redirection.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

The local program intentionally excludes loads, stores, and branches from acceptance criteria.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
