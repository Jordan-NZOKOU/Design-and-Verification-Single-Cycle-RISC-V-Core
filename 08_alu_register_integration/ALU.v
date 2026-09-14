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
 * Module: ALU
 *  *
 *  * Combinational arithmetic/logic unit for ADD, SUB, AND, OR, and signed SLT.
 *  * The result drives Zero and Negative continuously. Carry and OverFlow are
 *  * meaningful for arithmetic operations and deterministically cleared for logic
 *  * operations or unsupported controls.
 *  *
 *  * The explicit defaults at the start of the always block fully assign every
 *  * procedural output and prevent accidental latch inference.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Operation roles in the processor:
//   ADD supports arithmetic, immediate arithmetic, and LW/SW address generation.
//   SUB supports arithmetic and BEQ equality evaluation through the Zero flag.
//   AND/OR implement bitwise operations. SLT performs a signed comparison.
//
// Flag interpretation:
//   Carry is an unsigned property of the 33-bit arithmetic result. OverFlow is a
//   signed two's-complement property. They are intentionally calculated with
//   different equations and must not be treated as synonyms.
//
// Combinational safety:
//   Defaults at the start of always @(*) guarantee every procedural output is
//   assigned even for unsupported controls. This prevents latches and makes an
//   illegal internal control value deterministic during simulation.
//
// Signed comparison:
//   Explicit $signed casts are used instead of subtracting and reading Result[31],
//   because subtraction sign alone is not a valid signed less-than result when
//   signed overflow occurs.
// -----------------------------------------------------------------------------
// 32-bit arithmetic and logic unit.
// ALUControl encoding:
//   3'b000: ADD
//   3'b001: SUB
//   3'b010: AND
//   3'b011: OR
//   3'b101: signed set-less-than
module ALU(
    input  wire [31:0] A,
    input  wire [31:0] B,
    input  wire [2:0]  ALUControl,
    output reg  [31:0] Result,
    output reg         OverFlow,
    output reg         Carry,
    output wire        Zero,
    output wire        Negative
);

    localparam [2:0] ALU_ADD = 3'b000;
    localparam [2:0] ALU_SUB = 3'b001;
    localparam [2:0] ALU_AND = 3'b010;
    localparam [2:0] ALU_OR  = 3'b011;
    localparam [2:0] ALU_SLT = 3'b101;

    // Reevaluate whenever any input changes; every output receives a default.
    always @(*) begin
        Result   = 32'b0;
        Carry    = 1'b0;
        OverFlow = 1'b0;

        case (ALUControl)
            // ADD retains unsigned carry and computes signed overflow separately.
            ALU_ADD: begin
                // Extend the addition by one bit to retain the unsigned carry.
                {Carry, Result} = {1'b0, A} + {1'b0, B};
                OverFlow = (~(A[31] ^ B[31])) & (Result[31] ^ A[31]);
            end

            // SUB uses A + ~B + 1; Carry is the resulting no-borrow indication.
            ALU_SUB: begin
                // Two's-complement subtraction: A - B = A + ~B + 1.
                {Carry, Result} = {1'b0, A} + {1'b0, ~B} + 33'b1;
                OverFlow = (A[31] ^ B[31]) & (Result[31] ^ A[31]);
            end

            // Bitwise logical operations intentionally clear arithmetic flags.
            ALU_AND: Result = A & B;
            ALU_OR:  Result = A | B;
            // Explicit signed casts are required for two's-complement comparison.
            ALU_SLT: Result = ($signed(A) < $signed(B)) ? 32'd1 : 32'd0;

            default: begin
                Result   = 32'b0;
                Carry    = 1'b0;
                OverFlow = 1'b0;
            end
        endcase
    end

    // These status outputs are functions of the resolved Result value.
    assign Zero     = (Result == 32'b0);
    assign Negative = Result[31];

endmodule

`default_nettype wire
