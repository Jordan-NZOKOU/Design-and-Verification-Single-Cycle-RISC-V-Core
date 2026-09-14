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
 * Module: ALU_Decoder
 *  *
 *  * Second-level control decoder. ALUOp forces ADD for address generation, forces
 *  * SUB for BEQ comparison, or requests funct3/funct7 decoding for ALU classes.
 *  * The opcode participates in ADD/SUB discrimination so I-type immediate bits
 *  * cannot be mistaken for an R-type funct7 field.
 *  *
 *  * Unsupported combinations resolve to ADD as a deterministic benign default.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Two-level decode rationale:
//   ALUOp handles operations implied by the instruction class. Function fields
//   are consulted only for ALU instruction classes, reducing duplicated logic.
//
// ADD/SUB qualification:
//   funct3=000 is shared by ADD, SUB, and ADDI. SUB is selected only when the
//   opcode identifies the R-type class and funct7[5] is set. This prevents an
//   immediate bit in ADDI from being misread as a SUB qualifier.
//
// Deterministic fallback:
//   Unsupported function combinations resolve to ADD. The main decoder still
//   controls whether a register/memory side effect is legal.
// -----------------------------------------------------------------------------
// Secondary decoder that maps ALUOp and instruction function fields to the
// internal ALUControl encoding.
module ALU_Decoder(
    input  wire [1:0] ALUOp,
    input  wire [2:0] funct3,
    input  wire [6:0] funct7,
    input  wire [6:0] op,
    output reg  [2:0] ALUControl
);

    // ALUOp determines whether operation decoding is forced or function-based.
    always @(*) begin
        case (ALUOp)
            2'b00: ALUControl = 3'b000; // Address generation for LW/SW.
            2'b01: ALUControl = 3'b001; // Equality comparison for BEQ.

            // R-type or I-type ALU class. funct3 selects the operation family.
            2'b10: begin
                case (funct3)
                    // ADD/ADDI unless both R-type qualification and funct7[5] select SUB.
                    3'b000: begin
                        // SUB requires an R-type opcode and funct7[5]=1.
                        if (op[5] && funct7[5])
                            ALUControl = 3'b001;
                        else
                            ALUControl = 3'b000;
                    end
                    3'b010: ALUControl = 3'b101; // SLT / SLTI
                    3'b110: ALUControl = 3'b011; // OR / ORI
                    3'b111: ALUControl = 3'b010; // AND / ANDI
                    default: ALUControl = 3'b000;
                endcase
            end

            default: ALUControl = 3'b000;
        endcase
    end

endmodule

`default_nettype wire
