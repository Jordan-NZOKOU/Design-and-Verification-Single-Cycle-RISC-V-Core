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

"""Execute the implemented RV32I subset and validate the final program image.

This model is intentionally independent from the Verilog hierarchy. It provides
an architectural oracle for program images, register state, memory state, store
counts, and control-flow trajectory.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT / "11_final_processor" / "program.hex"


def sign_extend(value: int, bits: int) -> int:
    """Interpret *value* as a signed two's-complement integer of *bits* width."""
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def u32(value: int) -> int:
    """Wrap an integer to the 32-bit unsigned architectural width."""
    return value & 0xFFFFFFFF


def s32(value: int) -> int:
    """Interpret the low 32 bits of an integer as signed two's complement."""
    return sign_extend(value & 0xFFFFFFFF, 32)


@dataclass
class Machine:
    """Minimal architectural state and execution semantics for the project ISA."""

    program: list[int]
    registers: list[int] = field(default_factory=lambda: [0] * 32)
    memory: list[int] = field(default_factory=lambda: [0] * 256)
    pc: int = 0
    cycles: int = 0
    store_count: int = 0
    taken_branches: int = 0
    visited_pcs: list[int] = field(default_factory=list)

    def fetch(self) -> int:
        """Fetch one aligned word, returning RV32I NOP beyond the program image."""
        index = self.pc >> 2
        if index >= len(self.program):
            return 0x00000013
        return self.program[index]

    def step(self) -> None:
        """Execute exactly one instruction and update architectural state."""
        instruction = self.fetch()
        current_pc = self.pc
        next_pc = u32(current_pc + 4)
        self.visited_pcs.append(current_pc)

        # Common RISC-V fields are extracted once and reused by all classes.
        opcode = instruction & 0x7F
        rd = (instruction >> 7) & 0x1F
        funct3 = (instruction >> 12) & 0x07
        rs1 = (instruction >> 15) & 0x1F
        rs2 = (instruction >> 20) & 0x1F
        funct7 = (instruction >> 25) & 0x7F
        a = self.registers[rs1]
        b = self.registers[rs2]
        write_value: int | None = None

        # R-type arithmetic and logic.
        if opcode == 0x33:
            if funct3 == 0b000 and funct7 == 0x00:
                write_value = u32(a + b)
            elif funct3 == 0b000 and funct7 == 0x20:
                write_value = u32(a - b)
            elif funct3 == 0b111 and funct7 == 0x00:
                write_value = a & b
            elif funct3 == 0b110 and funct7 == 0x00:
                write_value = a | b
            elif funct3 == 0b010 and funct7 == 0x00:
                write_value = 1 if s32(a) < s32(b) else 0
            else:
                raise ValueError(f"Unsupported R-type instruction 0x{instruction:08X}")

        # I-type ALU operations.
        elif opcode == 0x13:
            immediate = sign_extend(instruction >> 20, 12)
            if funct3 == 0b000:
                write_value = u32(a + immediate)
            elif funct3 == 0b111:
                write_value = a & u32(immediate)
            elif funct3 == 0b110:
                write_value = a | u32(immediate)
            elif funct3 == 0b010:
                write_value = 1 if s32(a) < immediate else 0
            else:
                raise ValueError(f"Unsupported I-type instruction 0x{instruction:08X}")

        # Aligned 32-bit load.
        elif opcode == 0x03 and funct3 == 0b010:
            immediate = sign_extend(instruction >> 20, 12)
            address = u32(a + immediate)
            if address & 0x3:
                raise ValueError(f"Misaligned LW address 0x{address:08X}")
            write_value = self.memory[address >> 2]

        # Aligned 32-bit store.
        elif opcode == 0x23 and funct3 == 0b010:
            immediate_bits = ((instruction >> 25) << 5) | ((instruction >> 7) & 0x1F)
            immediate = sign_extend(immediate_bits, 12)
            address = u32(a + immediate)
            if address & 0x3:
                raise ValueError(f"Misaligned SW address 0x{address:08X}")
            self.memory[address >> 2] = b
            self.store_count += 1

        # BEQ with PC-relative B-type immediate.
        elif opcode == 0x63 and funct3 == 0b000:
            immediate_bits = (
                (((instruction >> 31) & 0x1) << 12)
                | (((instruction >> 7) & 0x1) << 11)
                | (((instruction >> 25) & 0x3F) << 5)
                | (((instruction >> 8) & 0x0F) << 1)
            )
            offset = sign_extend(immediate_bits, 13)
            if a == b:
                next_pc = u32(current_pc + offset)
                self.taken_branches += 1

        else:
            raise ValueError(
                f"Unsupported instruction 0x{instruction:08X} at PC=0x{current_pc:08X}"
            )

        # x0 is never written. Every result and PC update is constrained to 32 bits.
        if write_value is not None and rd != 0:
            self.registers[rd] = u32(write_value)
        self.registers[0] = 0
        self.pc = next_pc
        self.cycles += 1


def load_program(path: Path) -> list[int]:
    """Read a $readmemh-compatible image while ignoring license comment lines."""
    words: list[int] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith(("//", "#", "/*", "*", "*/")):
            continue
        # Strip an optional trailing single-line comment without accepting
        # arbitrary non-hex content as an instruction.
        line = line.split("//", 1)[0].strip()
        try:
            words.append(int(line, 16))
        except ValueError as exc:
            raise ValueError(f"Invalid HEX word on line {line_number}: {line}") from exc
    return words


def validate(machine: Machine) -> None:
    """Apply the release-level architectural acceptance criteria."""
    expected_registers = {
        5: 0x00000005,
        6: 0x00000004,
        7: 0x00000005,
        8: 0x00000004,
        9: 0x00000001,
        10: 0x00000001,
        11: 0x00000005,
        12: 0x00000002,
        13: 0xFFFFFFFF,
        14: 0x00000001,
        15: 0xFFFFFFFF,
    }
    failures: list[str] = []

    for index, expected in expected_registers.items():
        actual = machine.registers[index]
        if actual != expected:
            failures.append(f"x{index}: actual=0x{actual:08X} expected=0x{expected:08X}")

    for index, expected in {0: 5, 1: 2}.items():
        actual = machine.memory[index]
        if actual != expected:
            failures.append(f"mem[{index}]: actual=0x{actual:08X} expected=0x{expected:08X}")

    if machine.store_count != 2:
        failures.append(f"store_count: actual={machine.store_count} expected=2")
    if 0x24 in machine.visited_pcs:
        failures.append("PC=0x24 was visited even though the taken branch must skip it")
    if machine.taken_branches < 2:
        failures.append(f"taken_branches: actual={machine.taken_branches} expected>=2")
    if machine.pc != 0x3C:
        failures.append(f"final PC: actual=0x{machine.pc:08X} expected=0x0000003C")

    if failures:
        raise AssertionError("Reference-model validation failed:\n- " + "\n- ".join(failures))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--cycles", type=int, default=40)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    machine = Machine(load_program(args.image))
    for _ in range(args.cycles):
        machine.step()
    validate(machine)
    print(
        "Reference model passed: "
        f"cycles={machine.cycles}, stores={machine.store_count}, "
        f"taken_branches={machine.taken_branches}, final_pc=0x{machine.pc:08X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
