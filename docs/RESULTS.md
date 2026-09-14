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

# Expected Results

## Unit milestones

Each milestone must end with one of the following success messages:

```text
TEST MUX PASSED
TEST PC AND ADDER PASSED
TEST ALU PASSED
TEST REGISTER FILE PASSED
TEST SIGN EXTEND PASSED
TEST MEMORIES PASSED
TEST CONTROL UNIT PASSED
TEST ALU AND REGISTER INTEGRATION PASSED
TEST LOAD/STORE INTEGRATION PASSED
TEST BRANCH INTEGRATION PASSED
TEST FINAL PROCESSOR PASSED
```

## Final architectural state

| Location | Expected value |
|---|---:|
| x5 | `0x00000005` |
| x6 | `0x00000004` |
| x7 | `0x00000005` |
| x8 | `0x00000004` |
| x9 | `0x00000001` |
| x10 | `0x00000001` |
| x11 | `0x00000005` |
| x12 | `0x00000002` |
| x13 | `0xFFFFFFFF` |
| x14 | `0x00000001` |
| x15 | `0xFFFFFFFF` |
| mem[0] | `0x00000005` |
| mem[1] | `0x00000002` |
| final PC | `0x0000003C` |

Additional evidence:

- exactly two store transactions;
- `PC=0x00000024` is not observed because the forward BEQ skips it;
- taken branch count is at least two because the terminal loop also branches;
- reference-model run completes in the documented observation window.

![Final regression](../13_diagrams/svg/22_final_regression.svg)

## Failure interpretation

A register mismatch usually points to decode, ALU operand selection, or
write-back. A correct address with wrong memory data points to the RD2/store path.
A wrong PC sequence points to B-immediate reconstruction, Zero, PCSrc, target
addition, or next-PC muxing. The report contains a symptom-oriented debug guide.
