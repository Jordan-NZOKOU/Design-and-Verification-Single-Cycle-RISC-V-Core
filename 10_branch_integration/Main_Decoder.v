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
 * Module: Main_Decoder
 *  *
 *  * First-level control decoder. The seven-bit opcode selects the instruction
 *  * class and generates coarse datapath controls plus ALUOp. Safe defaults are
 *  * assigned before the case statement, ensuring unsupported opcodes cannot write
 *  * registers, modify memory, or redirect control flow.
 *  *
 *  * This separation keeps opcode-class policy independent from funct3/funct7 ALU
 *  * selection, which is delegated to ALU_Decoder.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Decoder responsibility:
//   This level identifies the instruction class from the opcode and produces
//   datapath-wide controls. It does not select the exact R/I ALU operation.
//
// Safety policy:
//   Defaults deassert RegWrite, MemWrite, and Branch. Consequently an unsupported
//   opcode cannot create an architectural side effect in this subset.
//
// ALUOp abstraction:
//   00 forces ADD for address generation, 01 forces SUB for branch comparison,
//   and 10 delegates operation selection to funct3/funct7 decoding.
//
// Immediate selection:
//   I, S, and B formats are encoded separately so the immediate unit remains
//   independent of the opcode table.
// -----------------------------------------------------------------------------
// Main opcode decoder for the implemented RV32I subset.
module Main_Decoder(
    input  wire [6:0] Op,
    output reg        RegWrite,
    output reg [1:0]  ImmSrc,
    output reg        ALUSrc,
    output reg        MemWrite,
    output reg        ResultSrc,
    output reg        Branch,
    output reg [1:0]  ALUOp
);

    localparam [6:0] OP_LOAD   = 7'b0000011;
    localparam [6:0] OP_STORE  = 7'b0100011;
    localparam [6:0] OP_RTYPE  = 7'b0110011;
    localparam [6:0] OP_BRANCH = 7'b1100011;
    localparam [6:0] OP_ITYPE  = 7'b0010011;

    // Defaults form a fail-safe no-write/no-branch control vector.
    always @(*) begin
        // Safe defaults disable all architectural state updates.
        RegWrite  = 1'b0;
        ImmSrc    = 2'b00;
        ALUSrc    = 1'b0;
        MemWrite  = 1'b0;
        ResultSrc = 1'b0;
        Branch    = 1'b0;
        ALUOp     = 2'b00;

        case (Op)
            // LW: add base+I-immediate, select memory data, write rd.
            OP_LOAD: begin
                RegWrite  = 1'b1;
                ImmSrc    = 2'b00;
                ALUSrc    = 1'b1;
                ResultSrc = 1'b1;
                ALUOp     = 2'b00;
            end

            // SW: add base+S-immediate and assert the memory write enable.
            OP_STORE: begin
                ImmSrc   = 2'b01;
                ALUSrc   = 1'b1;
                MemWrite = 1'b1;
                ALUOp    = 2'b00;
            end

            // Register-register operation; ALU_Decoder examines function fields.
            OP_RTYPE: begin
                RegWrite = 1'b1;
                ALUOp    = 2'b10;
            end

            // BEQ class: B-immediate and subtraction-based equality comparison.
            OP_BRANCH: begin
                ImmSrc = 2'b10;
                Branch = 1'b1;
                ALUOp  = 2'b01;
            end

            // Register-immediate ALU operation selected by funct3.
            OP_ITYPE: begin
                RegWrite = 1'b1;
                ALUSrc   = 1'b1;
                ALUOp    = 2'b10;
            end

            default: begin
                // Retain safe defaults for unsupported opcodes.
            end
        endcase
    end

endmodule

`default_nettype wire
