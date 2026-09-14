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
 * Module: Instruction_Memory
 *  *
 *  * Behavioral asynchronous instruction ROM loaded with $readmemh. External
 *  * addresses are byte addresses; bits [1:0] are dropped to index 32-bit words.
 *  * Unused locations are initialized to RV32I NOP before loading the image, which
 *  * avoids X propagation when execution reaches padding.
 *  *
 *  * During reset the read output is forced to NOP.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Interface units:
//   A is a byte address from the architectural PC. The storage array is indexed
//   in 32-bit words, so bits [1:0] are alignment bits and [9:2] select one entry.
//
// Initialization:
//   $readmemh loads one 32-bit instruction word per line from MEMFILE. The file
//   parameter allows each integration milestone to carry a self-contained image.
//
// Reset visibility:
//   The ROM contents are not erased. Instead, the output is masked with the
//   canonical ADDI x0,x0,0 NOP while rst_n is low, keeping fetch deterministic.
//
// Modeling boundary:
//   This asynchronous behavioral ROM is convenient for simulation; a deployed
//   target may require a synchronous memory wrapper or instruction bus.
// -----------------------------------------------------------------------------
// Asynchronous instruction memory. A is byte-addressed; bits [1:0] are
// discarded to select a 32-bit word.
module Instruction_Memory #(
    parameter DEPTH      = 256,
    parameter ADDR_WIDTH = 8,
    parameter MEMFILE    = "program.hex"
)(
    input  wire        rst_n,
    input  wire [31:0] A,
    output wire [31:0] RD
);

    // Word array; the external byte address is converted at the read expression.
    reg [31:0] mem [0:DEPTH-1];
    integer i;

    // Simulation-time initialization and program-image loading.
    initial begin
        // Fill unused locations with the RV32I NOP encoding before loading the
        // program image. This prevents X propagation beyond the program end.
        for (i = 0; i < DEPTH; i = i + 1)
            mem[i] = 32'h00000013;

        $readmemh(MEMFILE, mem);
    end

    // Asynchronous fetch; reset substitutes a side-effect-free NOP.
    assign RD = (!rst_n) ? 32'h00000013 : mem[A[ADDR_WIDTH+1:2]];

endmodule

`default_nettype wire
