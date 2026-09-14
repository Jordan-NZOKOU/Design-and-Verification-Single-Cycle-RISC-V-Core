#!/usr/bin/env python3
# Copyright 2026 Jordan Nzokou and Doeg Tiozang
# Project: Nexvantis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Two-pass assembler for the exact RV32I subset implemented by Nexvantis.

Supported instructions: ADD, SUB, AND, OR, SLT, ADDI, ANDI, ORI, SLTI,
LW, SW, BEQ, and NOP. Labels are supported as BEQ targets.

Example:
    python3 mini_assembler.py final_program.asm final_program_generated.hex
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REGISTER_ALIASES = {f"x{index}": index for index in range(32)}

# The generated HEX header is accepted by $readmemh as single-line comments and
# ensures that data artifacts carry the same project notice as source files.
HEX_NOTICE = """// Copyright 2026 Jordan Nzokou and Doeg Tiozang
// Project: Nexvantis
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

"""


def parse_register(token: str) -> int:
    """Translate x0..x31 into the five-bit architectural register index."""
    key = token.strip().lower()
    try:
        return REGISTER_ALIASES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown register: {token}") from exc


def parse_immediate(token: str) -> int:
    """Parse decimal, hexadecimal, binary, octal, or signed Python-style text."""
    return int(token.strip(), 0)


def require_signed_range(value: int, bits: int, context: str) -> None:
    """Reject an immediate that cannot be represented in a signed field."""
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    if not minimum <= value <= maximum:
        raise ValueError(
            f"{context} immediate {value} is outside the signed {bits}-bit range "
            f"[{minimum}, {maximum}]"
        )


def encode_r(funct7: int, rs2: int, rs1: int, funct3: int, rd: int) -> int:
    """Pack one R-type instruction using opcode 0x33."""
    return (
        ((funct7 & 0x7F) << 25)
        | ((rs2 & 0x1F) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x07) << 12)
        | ((rd & 0x1F) << 7)
        | 0x33
    )


def encode_i(immediate: int, rs1: int, funct3: int, rd: int, opcode: int) -> int:
    """Pack one 12-bit signed I-type immediate instruction."""
    require_signed_range(immediate, 12, "I-type")
    return (
        ((immediate & 0xFFF) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x07) << 12)
        | ((rd & 0x1F) << 7)
        | opcode
    )


def encode_s(immediate: int, rs2: int, rs1: int, funct3: int = 0b010) -> int:
    """Split and pack one 12-bit signed S-type store immediate."""
    require_signed_range(immediate, 12, "S-type")
    value = immediate & 0xFFF
    return (
        (((value >> 5) & 0x7F) << 25)
        | ((rs2 & 0x1F) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x07) << 12)
        | ((value & 0x1F) << 7)
        | 0x23
    )


def encode_b(offset: int, rs2: int, rs1: int, funct3: int = 0b000) -> int:
    """Reorder and pack one signed B-type branch displacement."""
    if offset % 2 != 0:
        raise ValueError("BEQ offset must be aligned to 2 bytes")
    require_signed_range(offset, 13, "B-type")
    value = offset & 0x1FFF
    return (
        (((value >> 12) & 0x01) << 31)
        | (((value >> 5) & 0x3F) << 25)
        | ((rs2 & 0x1F) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x07) << 12)
        | (((value >> 1) & 0x0F) << 8)
        | (((value >> 11) & 0x01) << 7)
        | 0x63
    )


def clean_lines(text: str) -> list[str]:
    """Remove blank lines and # or // comments from assembly source."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].split("//", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def assemble(text: str) -> list[int]:
    """Resolve labels in pass 1, then encode instructions in pass 2."""
    lines = clean_lines(text)
    labels: dict[str, int] = {}
    instructions: list[tuple[int, str]] = []
    pc = 0

    # Pass 1 records label byte addresses and preserves the corresponding
    # instruction address for branch displacement calculation.
    for original_line in lines:
        line = original_line
        while ":" in line:
            label, line = line.split(":", 1)
            label = label.strip()
            if not label:
                raise ValueError(f"Empty label in line: {original_line}")
            if label in labels:
                raise ValueError(f"Duplicate label: {label}")
            labels[label] = pc
            line = line.strip()
            if not line:
                break
        if line:
            instructions.append((pc, line))
            pc += 4

    words: list[int] = []

    # Pass 2 parses operands, validates field ranges, and emits 32-bit words.
    for pc, line in instructions:
        normalized = line.replace(",", " ")
        parts = normalized.split(None, 1)
        mnemonic = parts[0].lower()
        arguments = parts[1] if len(parts) > 1 else ""
        tokens = [token for token in re.split(r"[\s()]+", arguments) if token]

        if mnemonic in {"add", "sub", "and", "or", "slt"}:
            if len(tokens) != 3:
                raise ValueError(f"Expected rd, rs1, rs2 at PC={pc:#x}: {line}")
            rd, rs1, rs2 = map(parse_register, tokens)
            funct7, funct3 = {
                "add": (0x00, 0b000),
                "sub": (0x20, 0b000),
                "and": (0x00, 0b111),
                "or":  (0x00, 0b110),
                "slt": (0x00, 0b010),
            }[mnemonic]
            word = encode_r(funct7, rs2, rs1, funct3, rd)

        elif mnemonic in {"addi", "andi", "ori", "slti"}:
            if len(tokens) != 3:
                raise ValueError(f"Expected rd, rs1, imm at PC={pc:#x}: {line}")
            rd = parse_register(tokens[0])
            rs1 = parse_register(tokens[1])
            immediate = parse_immediate(tokens[2])
            funct3 = {
                "addi": 0b000,
                "slti": 0b010,
                "ori":  0b110,
                "andi": 0b111,
            }[mnemonic]
            word = encode_i(immediate, rs1, funct3, rd, 0x13)

        elif mnemonic == "lw":
            if len(tokens) != 3:
                raise ValueError(f"Expected rd, imm(rs1) at PC={pc:#x}: {line}")
            rd = parse_register(tokens[0])
            immediate = parse_immediate(tokens[1])
            rs1 = parse_register(tokens[2])
            word = encode_i(immediate, rs1, 0b010, rd, 0x03)

        elif mnemonic == "sw":
            if len(tokens) != 3:
                raise ValueError(f"Expected rs2, imm(rs1) at PC={pc:#x}: {line}")
            rs2 = parse_register(tokens[0])
            immediate = parse_immediate(tokens[1])
            rs1 = parse_register(tokens[2])
            word = encode_s(immediate, rs2, rs1)

        elif mnemonic == "beq":
            if len(tokens) != 3:
                raise ValueError(f"Expected rs1, rs2, target at PC={pc:#x}: {line}")
            rs1 = parse_register(tokens[0])
            rs2 = parse_register(tokens[1])
            target = tokens[2]
            offset = labels[target] - pc if target in labels else parse_immediate(target)
            word = encode_b(offset, rs2, rs1)

        elif mnemonic == "nop":
            if tokens:
                raise ValueError(f"NOP does not accept operands at PC={pc:#x}: {line}")
            word = 0x00000013

        else:
            raise ValueError(f"Unsupported instruction at PC={pc:#x}: {line}")

        words.append(word)

    return words


def write_hex(words: list[int], destination: Path) -> None:
    """Write a license-prefixed, $readmemh-compatible uppercase HEX image."""
    destination.write_text(
        HEX_NOTICE + "".join(f"{word:08X}\n" for word in words),
        encoding="ascii",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Assembly source file")
    parser.add_argument("destination", type=Path, help="Output HEX file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    words = assemble(args.source.read_text(encoding="utf-8"))
    write_hex(words, args.destination)
    print(f"Wrote {len(words)} instruction(s) to {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
