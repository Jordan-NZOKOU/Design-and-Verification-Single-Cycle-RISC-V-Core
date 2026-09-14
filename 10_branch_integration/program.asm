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

# Taken-branch integration program.
addi x1, x0, 1
addi x2, x0, 1
beq  x1, x2, taken
addi x3, x0, 99       # Must be skipped.
taken:
addi x3, x0, 7
sw   x3, 0(x0)
finish:
beq  x0, x0, finish
