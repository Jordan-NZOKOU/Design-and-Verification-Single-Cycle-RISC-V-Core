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

`timescale 1ns/1ps
`default_nettype none

/**
 * Module: PC_Adder
 *  *
 *  * Stateless 32-bit adder used for both PC+4 and PC+ImmExt. Arithmetic wraps
 *  * modulo 2^32; carry-out is intentionally not exposed because this project does
 *  * not implement address-overflow exceptions.
 *  *
 *  * Contract: c continuously equals a+b.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Reuse:
//   One instance computes the sequential address PC+4. A second computes the
//   PC-relative branch target PC+ImmExt. Their arithmetic behavior is identical.
//
// Width behavior:
//   Verilog retains the 32-bit output width, so a carry beyond bit 31 is dropped.
//   The current processor does not implement address-overflow exceptions.
//
// Timing:
//   This is a combinational path and contributes to next-PC timing. It contains
//   no reset because it stores no state.
// -----------------------------------------------------------------------------
// 32-bit combinational adder used for PC+4 and branch-target generation.
module PC_Adder(
    input  wire [31:0] a,
    input  wire [31:0] b,
    output wire [31:0] c
);

    // The result is available combinationally and wraps naturally at 32 bits.
    assign c = a + b;

endmodule

`default_nettype wire
