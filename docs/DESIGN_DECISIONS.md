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

# Design Decisions

## DD-01 - Single-cycle microarchitecture

**Decision:** execute each supported instruction in one clock period.

**Reason:** exposes the complete datapath and control relationships without
pipeline hazards. It is appropriate for a compact portfolio project.

**Trade-off:** the clock period is constrained by the longest combinational path.

## DD-02 - Separate instruction and data memories

**Decision:** use a Harvard organization.

**Reason:** instruction fetch and data access may occur in the same cycle without
a dual-port shared memory.

**Trade-off:** the model does not represent a unified external bus or cache.

## DD-03 - Synchronous active-low reset

**Decision:** state observes `rst_n` on the rising edge.

**Reason:** keeps all state transitions edge-aligned and makes the testbench
contract explicit.

**Trade-off:** asserting reset between edges does not change outputs immediately.

## DD-04 - Full register/memory reset in simulation

**Decision:** clear arrays for deterministic test results.

**Reason:** removes uninitialized-state noise and makes beginner/reviewer traces
repeatable.

**Trade-off:** target technologies may not infer efficient memories with this
reset style. Production integration would adapt the storage implementation.

## DD-05 - Two-level control decode

**Decision:** split opcode-class and ALU-function decoding.

**Reason:** address generation and branch subtraction become forced coarse
operations, while R/I ALU classes share function decoding.

## DD-06 - Safe deterministic defaults

**Decision:** unsupported decodes deassert writes and default ALU output/control.

**Reason:** avoids latch inference and unintended architectural side effects.

**Trade-off:** no illegal-instruction trap is generated.

## DD-07 - Direct signed SLT expression

**Decision:** use `$signed(A) < $signed(B)`.

**Reason:** avoids incorrect use of a subtraction sign bit when signed overflow
occurs.

## DD-08 - Local RTL copies in integration milestones

**Decision:** keep each milestone independently compilable.

**Reason:** a reviewer can enter any directory and run it without global source
paths.

**Risk control:** repository preflight rejects divergence among repeated modules.

## DD-09 - Observation-only debug ports

**Decision:** expose selected internal datapath signals at the top level.

**Reason:** enables integration tests without altering control/state behavior.

## DD-10 - Generated diagrams and report

**Decision:** commit source and rendered visual assets.

**Reason:** figures remain reproducible and editable, while GitHub and the PDF
can consume optimized formats directly.
