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

"""Unit tests for field encoders, label resolution, and input validation."""

from __future__ import annotations

import unittest

from mini_assembler import assemble, encode_b, encode_i, encode_r, encode_s


class EncodingTests(unittest.TestCase):
    """Check known instruction words and deliberately invalid inputs."""

    def test_r_type_add(self) -> None:
        self.assertEqual(encode_r(0x00, 6, 5, 0b000, 7), 0x006283B3)

    def test_i_type_negative(self) -> None:
        self.assertEqual(encode_i(-1, 0, 0b000, 13, 0x13), 0xFFF00693)

    def test_s_type(self) -> None:
        self.assertEqual(encode_s(4, 12, 0), 0x00C02223)

    def test_b_type_backward(self) -> None:
        self.assertEqual(encode_b(0, 0, 0), 0x00000063)

    def test_branch_label_resolution(self) -> None:
        words = assemble("start: addi x1, x0, 1\nbeq x1, x1, start\n")
        self.assertEqual(words, [0x00100093, 0xFE108EE3])

    def test_unknown_register_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown register"):
            assemble("addi x32, x0, 1\n")

    def test_unaligned_branch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "aligned"):
            assemble("beq x0, x0, 3\n")

    def test_duplicate_label_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate label"):
            assemble("loop: nop\nloop: nop\n")


if __name__ == "__main__":
    unittest.main()
