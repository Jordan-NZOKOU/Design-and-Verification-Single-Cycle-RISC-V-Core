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

# Milestone 01 - Parameterized 2:1 Multiplexer

<p align="center">
  <img src="../13_diagrams/svg/04_mux_structure.svg" alt="Milestone 01 - Parameterized 2:1 Multiplexer diagram" width="100%">
</p>

## Engineering objective

Implement and verify the smallest reusable combinational selection primitive in the processor. The same contract later selects the next PC, the ALU second operand, and register write-back data.

## Design overview

`Mux` is parameterized by `WIDTH` and has no clock, reset, enable, or internal state. A continuous conditional assignment expresses the full truth table: `s=0` forwards `a`; `s=1` forwards `b`. Because the output is combinational, a change on either selected input is visible after simulator delta-cycle propagation rather than after a clock edge.

### Architectural contract

The ternary operator maps directly to a 2:1 mux. `WIDTH` is an elaboration-time parameter, so there is no runtime width logic. The module uses `wire` ports and a continuous assignment, which makes the absence of storage explicit.

## Interface contract

| Signal | Direction | Contract |
|---|---|---|
| `a[WIDTH-1:0]` | input | Data input selected when `s=0` |
| `b[WIDTH-1:0]` | input | Data input selected when `s=1` |
| `s` | input | One-bit selector |
| `c[WIDTH-1:0]` | output | Selected data output |

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

- Drive distinct 32-bit values on `a` and `b`.
- Check `c == a` for `s=0`.
- Check `c == b` for `s=1`.
- Change an unselected input and confirm it does not alter the selected result.
- Use `!==` so an unknown output cannot be accepted as a valid value.

### Signals to inspect in GTKWave

`a`, `b`, `s`, `c`.

### Expected verdict

```text
TEST ... PASSED
```

A mismatch prints the observed and expected values before `$fatal` terminates the
simulation with a failing status.

## Files

| File | Role |
|---|---|
| `Mux.v` | Parameterized RTL implementation. |
| `Mux_tb.v` | Directed self-checking testbench with optional VCD output. |
| `run_questa.do` | QuestaSim/ModelSim compilation, execution, and VCD export. |
| `run_iverilog.sh` | Local Icarus Verilog wrapper. |

## Run

### QuestaSim or ModelSim

```bash
cd 01_mux
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
make test-project PROJECT=01_mux
```

### Waveform review

```bash
gtkwave *.vcd
```

Waveform review complements the automated checks; it is not the acceptance
criterion by itself.

## Review focus

Confirm that the module is purely combinational, that `WIDTH` controls every data port consistently, and that the testbench observes output changes without waiting for a clock.

A senior review should also confirm that comments describe intent and timing
rather than restating syntax, that all combinational paths have deterministic
defaults, and that the testbench proves the stated interface contract.

## Integration role

Three instances are used in `Single_Cycle_Top`: next-PC selection, ALU operand-B selection, and ALU/memory write-back selection.

The milestone is self-contained by design. Repeated core files are compared by
`scripts/repository_check.py` so independence does not permit silent divergence.

## Scope boundary

This block intentionally supports only two inputs. Priority muxes, one-hot selectors, tri-state buses, and glitch filtering are outside the project scope.

This boundary is intentional and is not an implicit compliance claim beyond the
behavior verified by this milestone.

## Related material

- [Root project overview](../README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification strategy](../docs/VERIFICATION_STRATEGY.md)
- [Complete English report](../00_documentation/nexvantis_rv32i_single_cycle_report_V6.pdf)
- [Diagram inventory](../13_diagrams/README.md)
