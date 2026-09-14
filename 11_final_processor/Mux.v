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
 * Module: Mux
 *  *
 *  * Parameterized, purely combinational 2:1 data selector. WIDTH controls all
 *  * data-port widths at elaboration time. The module has no clock, reset, enable,
 *  * storage, or tri-state behavior. It is reused for next-PC, ALU operand-B, and
 *  * register write-back selection in the final processor.
 *  *
 *  * Contract: s=0 forwards a; s=1 forwards b; c responds combinationally.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Data-path role:
//   This primitive is used wherever one of two 32-bit values must be selected
//   under control of a single Boolean decision. Keeping one parameterized module
//   avoids three independent mux implementations drifting apart.
//
// Timing contract:
//   There is no clocked boundary in this module. The output is a direct function
//   of the current inputs. A downstream state element decides when the selected
//   value is captured.
//
// Synthesis expectation:
//   For WIDTH=32 this infers 32 parallel 1-bit 2:1 mux cells (or equivalent LUT
//   logic). No latch, enable, or tri-state resource should be inferred.
// -----------------------------------------------------------------------------
// Parameterizable 2-to-1 combinational multiplexer.
module Mux #(
    parameter WIDTH = 32
)(
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    input  wire             s,
    output wire [WIDTH-1:0] c
);

    // Continuous assignment directly expresses the combinational truth table.
    assign c = s ? b : a;

endmodule

`default_nettype wire
