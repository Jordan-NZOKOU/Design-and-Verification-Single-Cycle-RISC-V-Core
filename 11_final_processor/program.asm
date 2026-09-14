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

# End-to-end program for the final processor regression.
addi x5,  x0, 5
addi x6,  x0, 4
or   x7,  x5, x6
and  x8,  x5, x6
sub  x9,  x5, x6
slt  x10, x6, x5
sw   x7,  0(x0)
lw   x11, 0(x0)
beq  x11, x7, equal
addi x12, x0, 99      # Must be skipped.
equal:
add  x12, x9, x10
sw   x12, 4(x0)
addi x13, x0, -1
slt  x14, x13, x0
or   x15, x13, x0
finish:
beq  x0, x0, finish
