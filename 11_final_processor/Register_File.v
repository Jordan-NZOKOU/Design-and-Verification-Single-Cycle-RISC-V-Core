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
 * Module: Register_File
 *  *
 *  * RV32I register file with two asynchronous read ports and one rising-edge
 *  * write port. Five-bit addresses select x0..x31. Writes to x0 are discarded and
 *  * reads from x0 are forced to zero. The active-low synchronous reset clears the
 *  * full array for deterministic simulation.
 *  *
 *  * Full-array reset is a documented modeling choice; a production technology
 *  * may require a different initialization strategy for efficient RAM inference.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Architectural contract:
//   A1/A2 select two independent source registers. A3 selects the destination.
//   The read ports are combinational; the write port commits on a rising edge.
//
// x0 invariant:
//   RISC-V requires x0 to read as zero and ignore writes. The implementation
//   enforces this both at the write guard and at each read output, so the rule
//   does not depend on initialization or software behavior.
//
// Reset/modeling note:
//   Clearing all 32 entries is convenient and deterministic for this behavioral
//   project. A target FPGA or ASIC flow may replace the array with a technology
//   macro whose reset/initialization constraints differ.
//
// Read-during-write behavior:
//   The project does not depend on same-address asynchronous read behavior during
//   the exact write edge; architectural checks sample after nonblocking updates.
// -----------------------------------------------------------------------------
// RV32I register file: two asynchronous read ports and one synchronous write
// port. Writes to x0 are discarded and reads from x0 always return zero.
module Register_File(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        WE3,
    input  wire [4:0]  A1,
    input  wire [4:0]  A2,
    input  wire [4:0]  A3,
    input  wire [31:0] WD3,
    output wire [31:0] RD1,
    output wire [31:0] RD2
);

    // Architectural storage for x0 through x31.
    reg [31:0] registers [0:31];
    integer i;

    // Full reset is retained for deterministic simulation. A production FPGA
    // or ASIC implementation may use a different initialization strategy.
    // Reset and writes are synchronous; read ports below remain combinational.
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1)
                registers[i] <= 32'b0;
        end
        else if (WE3 && (A3 != 5'd0)) begin
            registers[A3] <= WD3;
        end
    end

    // Explicit x0 bypasses protect the architectural invariant on both reads.
    assign RD1 = (A1 == 5'd0) ? 32'b0 : registers[A1];
    assign RD2 = (A2 == 5'd0) ? 32'b0 : registers[A2];

endmodule

`default_nettype wire
