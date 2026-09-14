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

"""Integration tests for the independent RV32I software reference model."""

from __future__ import annotations

import unittest
from pathlib import Path

from reference_model import Machine, load_program

ROOT = Path(__file__).resolve().parents[1]


class ReferenceModelIntegrationTests(unittest.TestCase):
    """Execute every integration image and compare its architectural outcome."""

    def run_program(self, directory: str, cycles: int) -> Machine:
        """Run one image for a fixed number of cycles and return final state."""
        model = Machine(load_program(ROOT / directory / "program.hex"))
        for _ in range(cycles):
            model.step()
        return model

    def test_arithmetic_integration(self) -> None:
        model = self.run_program("08_alu_register_integration", 8)
        self.assertEqual(model.registers[5:11], [5, 4, 5, 4, 1, 1])
        self.assertEqual(model.store_count, 0)
        self.assertEqual(model.memory[:2], [0, 0])

    def test_load_store_integration(self) -> None:
        model = self.run_program("09_load_store_integration", 8)
        self.assertEqual(model.registers[5], 42)
        self.assertEqual(model.registers[6], 42)
        self.assertEqual(model.registers[7], 84)
        self.assertEqual(model.memory[:2], [42, 84])
        self.assertEqual(model.store_count, 2)

    def test_branch_integration(self) -> None:
        model = self.run_program("10_branch_integration", 12)
        self.assertEqual(model.registers[1:4], [1, 1, 7])
        self.assertEqual(model.memory[0], 7)
        self.assertEqual(model.store_count, 1)
        self.assertNotIn(12, model.visited_pcs)
        self.assertEqual(model.pc, 24)

    def test_final_processor_program(self) -> None:
        model = self.run_program("11_final_processor", 22)
        expected = {
            5: 5,
            6: 4,
            7: 5,
            8: 4,
            9: 1,
            10: 1,
            11: 5,
            12: 2,
            13: 0xFFFF_FFFF,
            14: 1,
            15: 0xFFFF_FFFF,
        }
        for index, value in expected.items():
            self.assertEqual(model.registers[index], value, f"x{index}")
        self.assertEqual(model.memory[:2], [5, 2])
        self.assertEqual(model.store_count, 2)
        self.assertNotIn(0x24, model.visited_pcs)
        self.assertEqual(model.pc, 0x3C)


if __name__ == "__main__":
    unittest.main()
