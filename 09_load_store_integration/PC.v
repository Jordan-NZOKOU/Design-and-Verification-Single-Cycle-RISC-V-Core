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
 * Module: PC_Module
 *  *
 *  * Thirty-two-bit architectural program-counter register. rst_n is active-low
 *  * and synchronous: reset is sampled only on the rising edge. A nonblocking
 *  * assignment models the edge-triggered state update and prevents simulation
 *  * ordering artifacts when this block is integrated with other state elements.
 *  *
 *  * Contract: on posedge clk, PC becomes 0 when rst_n=0, otherwise PC_Next.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// State ownership:
//   PC is the only state in this module. PC_Next is computed elsewhere by the
//   combinational next-address network, so this block remains a simple register.
//
// Reset semantics:
//   rst_n is active-low but synchronous. Assertions or testbench checks must not
//   expect PC to clear until a rising edge samples rst_n=0.
//
// Clocking discipline:
//   A nonblocking assignment models simultaneous state updates across the full
//   processor and avoids order-dependent behavior at a shared clock edge.
// -----------------------------------------------------------------------------
// Program counter with an active-low synchronous reset.
module PC_Module(
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] PC_Next,
    output reg  [31:0] PC
);

    // Synchronous state transition: reset and normal update share the posedge.
    always @(posedge clk) begin
        if (!rst_n)
            PC <= 32'b0;
        else
            PC <= PC_Next;
    end

endmodule

`default_nettype wire
