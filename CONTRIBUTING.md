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

# Contributing

## Scope

Contributions should preserve the documented architecture unless an issue or
proposal explicitly changes the scope. Keep behavior changes separate from
comment/documentation-only changes.

## Development workflow

1. create a focused branch;
2. update RTL and the corresponding self-checking testbench together;
3. update the relevant milestone README and report section;
4. regenerate program images or diagrams when their source changes;
5. run `make preflight`;
6. run `make test` with Icarus Verilog;
7. run the applicable Questa script when available;
8. remove generated artifacts before committing.

## RTL style

- Verilog-2001 syntax;
- named port connections;
- nonblocking assignments for state;
- complete defaults for combinational procedural blocks;
- explicit signed casts where interpretation matters;
- `default_nettype none` around source modules;
- comments that explain contracts, timing, invariants, and non-obvious choices.

## Verification style

- deterministic initialization;
- `!==` for four-state checking;
- reusable tasks for repeated checks;
- a non-zero process result on failure;
- no acceptance based only on waveform screenshots;
- add trajectory/transaction evidence when final state is insufficient.

## Copyright and license headers

Every new file must carry the Nexvantis notice using the comment syntax accepted
by that file type. Binary diagrams and PDFs receive visible notice text and
metadata through the supplied generators.
