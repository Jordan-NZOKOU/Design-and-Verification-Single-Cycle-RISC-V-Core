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

# Software Tools and Program-Image Generation

## Engineering objective

Provide a transparent, testable software path from readable assembly source to
the instruction-memory image, plus an independent way to reason about expected
architectural behavior.

## Tool set

| File | Responsibility |
|---|---|
| `mini_assembler.py` | Two-pass assembler for the implemented instruction subset |
| `test_mini_assembler.py` | Unit tests for parsing, labels, immediates, range checks, and encodings |
| `final_program.asm` | Readable source of the final regression program |
| `final_program_generated.hex` | Reproducible assembler output |
| `../scripts/reference_model.py` | Independent decoder/execution model |
| `../scripts/test_reference_model.py` | Unit and integration tests for the model |

## Mini-assembler design

The assembler deliberately supports only the instructions implemented by the
RTL. Keeping the parser small makes every encoding rule reviewable.

### Pass 1 - labels and addresses

The source is normalized by removing comments and blank lines. Each instruction
advances the byte PC by four. A line ending with `:` records the current PC in
the symbol table. Duplicate labels are rejected.

### Pass 2 - encoding

Operands are parsed, labels are resolved, and immediate ranges/alignment are
validated before fields are packed into a 32-bit instruction. Branch labels are
converted to `target_pc - current_pc`, matching the RTL branch-target base.

### Supported source instructions

`ADD`, `SUB`, `AND`, `OR`, `SLT`, `ADDI`, `ANDI`, `ORI`, `SLTI`, `LW`, `SW`,
and `BEQ`.

## Deterministic output

The HEX file is one 32-bit word per line, suitable for `$readmemh`. It includes
a comment-form project notice that simulators ignore. Reproducibility is checked
with:

```bash
make assemble-check
```

The command assembles to a temporary file and performs a unified diff against
`11_final_processor/program.hex`.

## Run

```bash
python3 12_tools/mini_assembler.py \
  12_tools/final_program.asm \
  12_tools/final_program_generated.hex
```

Run unit tests:

```bash
python3 -m unittest discover -s 12_tools -p 'test_*.py' -v
```

Run the independent model:

```bash
python3 scripts/reference_model.py
```

## Verification strategy

The tests cover register parsing, signed immediate encoding, forward/backward
label resolution, load/store operand syntax, branch alignment, range rejection,
and reproduction of the final program image. The reference model separately
checks the final register file, data memory, store count, branch activity, and
terminal PC.

## Review focus

A reviewer should compare each encoder with the R/I/S/B instruction layouts,
confirm all range checks occur before masking, and verify that the model derives
state from decoded words rather than copying expected final values into state.

## Scope boundary

This is not a general GNU-compatible RISC-V assembler or ISA simulator. It has
no directives, relocation records, object files, linker, ABI pseudo-operations,
or unsupported instruction encodings.
