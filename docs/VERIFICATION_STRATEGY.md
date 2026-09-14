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

# Verification Strategy

## Verification objective

Demonstrate that each RTL contract and the final architectural behavior are
checked automatically, reproducibly, and with enough execution evidence to
localize failures.

![Verification workflow](../13_diagrams/svg/02_verification_workflow.svg)

## Layered plan

1. **Primitive blocks:** mux, PC/adders, ALU, register file, immediate unit.
2. **Infrastructure blocks:** instruction/data memories and control unit.
3. **Arithmetic integration:** verify instruction flow without memory writes.
4. **Memory integration:** verify LW/SW data and transaction counts.
5. **Branch integration:** verify PC trajectory and target side effects.
6. **Final regression:** combine all supported instruction classes.
7. **Independent model:** reproduce the same architectural state in Python.
8. **Repository preflight:** prove scripts, docs, links, notices, and images are coherent.

## Testbench pattern

Every testbench follows the same pattern:

- declare deterministic stimulus registers and observed wires;
- instantiate the DUT with named connections;
- optionally enable `$dumpfile/$dumpvars` under `DUMP_VCD`;
- centralize repeated comparisons in a task;
- use `!==` rather than `!=` to catch X/Z results;
- apply reset across a real clock edge for sequential DUTs;
- allow all planned checks to run by incrementing `error_count`;
- print a single PASS or invoke `$fatal` at completion.

## Functional coverage intent

This project does not use SystemVerilog covergroups. Coverage is documented as a
requirements-to-test matrix in each milestone README. Directed vectors cover
implemented operations, meaningful boundaries, reset behavior, safe defaults,
and architectural invariants.

## Integration evidence

Final-state checks alone can miss transient control bugs. Integration tests also
collect:

- exact `MemWrite` pulse count;
- observation of forbidden/skipped PC values;
- taken-branch count;
- final terminal-loop PC;
- ROM-image reproducibility;
- software-model agreement.

## Waveform policy

VCD waveforms are generated for debug and review, but a visual waveform is not
the sole pass criterion. Automated checks define acceptance. The report and
READMEs list the signals most useful when a check fails.

## Tool independence

The same Verilog sources can be run through QuestaSim/ModelSim or Icarus
Verilog. The Python model does not instantiate or parse internal Verilog state;
it decodes the HEX image independently.

## Known verification limits

- no constrained-random stimulus;
- no assertion language or formal proof;
- no code/functional coverage database;
- no gate-level or timing simulation;
- no CDC/RDC analysis because the design uses one clock domain;
- no unsupported ISA compliance claim.
