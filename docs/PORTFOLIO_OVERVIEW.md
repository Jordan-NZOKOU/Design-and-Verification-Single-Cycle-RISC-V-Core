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

# Portfolio Overview

## Purpose

Nexvantis demonstrates a complete small RTL project lifecycle rather than a
single isolated module: requirements, decomposition, implementation, directed
verification, progressive integration, software tooling, reproducible figures,
CI automation, and release documentation.

## What the repository demonstrates

### RTL design

- separation of state elements from combinational datapath logic;
- parameterized mux reuse;
- explicit reset and clock semantics;
- complete combinational assignments and deterministic defaults;
- RISC-V field extraction and immediate reconstruction;
- structural top-level integration;
- behavioral memory models with documented synthesis limitations.

### Verification

- self-checking testbenches with four-state comparisons;
- arithmetic corner cases and architectural invariants;
- transaction counts and PC-trajectory evidence;
- final-state checking across registers and memory;
- independent software reference modeling;
- simulator-neutral program-image reproduction.

### Engineering workflow

- eleven independently runnable milestones;
- manifest-driven Icarus regression;
- Questa/ModelSim scripts at project and repository levels;
- deterministic diagrams and English report generation;
- GitHub Actions and repository hygiene checks;
- explicit limits and extension roadmap.

## Suggested recruiter review

A 15-minute review can inspect the root README, architecture diagram, ALU,
control unit, final testbench, and the Scripts and automation section. A deeper
technical review should run preflight/regression, inspect waveforms around BEQ,
and compare the Verilog final state with the Python model.

## Evidence summary

The final program verifies twelve supported instructions, eleven register
values, two memory values, two stores, a skipped PC, branch activity, and a
terminal loop. The repository never relies on a screenshot as the only proof;
all evidence is reproducible from source.
