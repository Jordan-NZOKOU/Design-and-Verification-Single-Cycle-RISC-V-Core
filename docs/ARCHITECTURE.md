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

# Architecture

## Architectural model

Nexvantis is a 32-bit single-cycle processor implementing a documented RV32I
subset. Instruction memory and data memory are separate, avoiding a structural
conflict inside a single cycle. No pipeline register divides fetch, decode,
execute, memory, and write-back.

![Complete datapath](../13_diagrams/svg/21_final_datapath.svg)

## State elements

| State | Update event | Reset behavior |
|---|---|---|
| Program counter | rising edge | synchronous active-low reset to zero |
| Register file | rising edge when `RegWrite` | all entries clear; writes to x0 blocked |
| Data memory | rising edge when `MemWrite` | all entries clear in the behavioral model |

Instruction memory is initialized from a HEX file and is not modified by the
processor.

## Datapath by instruction class

### R-type ALU

The instruction selects `rs1`, `rs2`, and `rd`. `ALUSrc=0` forwards RD2 to the
ALU. `ResultSrc=0` returns ALUResult to the register file. `RegWrite=1` commits
at the rising edge.

### I-type ALU

The immediate unit reconstructs `instr[31:20]` and sign-extends it. `ALUSrc=1`
selects ImmExt. The ALU decoder uses `funct3`; the R-type SUB qualifier cannot
be activated by I-type immediate bits.

### LW

The ALU calculates `RD1 + ImmExt`. Data memory reads the addressed word
combinationally. `ResultSrc=1` selects ReadData and `RegWrite=1` commits it.

### SW

The ALU calculates `RD1 + ImmExt`. RD2 remains the store data. `MemWrite=1`
causes the memory write at the rising edge. `RegWrite=0` prevents a register
side effect.

### BEQ

The ALU subtracts RD2 from RD1. `Zero=1` means equal. `PCSrc` is asserted only
when the main decoder selected a branch and `funct3=000`. The target is current
`PC + ImmExt`; otherwise the PC receives `PC + 4`.

## Control partition

The main decoder handles instruction classes. The ALU decoder handles operation
selection. This avoids a monolithic truth table and makes address generation and
branch comparison explicit forced operations.

## Memory addressing

The processor exposes byte addresses. The behavioral arrays store 32-bit words,
so index `A[9:2]` discards the two alignment bits. Misaligned addresses are not
detected; the current scope assumes word alignment.

## Critical path

A representative load path is:

`PC -> instruction memory -> decoder/register read -> ALU address -> data memory -> result mux -> register input`.

The single-cycle clock period must accommodate the longest such path. The
project does not claim a target frequency or physical timing closure.

## Observation ports

`Single_Cycle_Top` exposes PC, instruction, MemWrite, ALUResult, WriteData, and
Result for verification. They are driven from internal signals and do not feed
back into the processor.
