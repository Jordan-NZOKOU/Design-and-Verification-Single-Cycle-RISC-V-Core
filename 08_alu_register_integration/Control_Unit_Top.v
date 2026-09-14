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
 * Module: Control_Unit_Top
 *  *
 *  * Composes the main decoder and ALU decoder, then qualifies the only supported
 *  * conditional branch. PCSrc is asserted only for a BEQ opcode/funct3 when the
 *  * ALU subtraction reports Zero.
 *  *
 *  * The control path is combinational; architectural state remains confined to
 *  * the PC, register file, and data memory.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Composition:
//   The main decoder supplies class-level controls and ALUOp. The ALU decoder
//   supplies the exact internal ALUControl. Neither block stores state.
//
// Branch qualification:
//   Branch alone identifies the branch opcode; Zero supplies the data-dependent
//   equality result; funct3==000 limits support to BEQ. All three must be true
//   before the next-PC mux may select PCTarget.
//
// Architectural side effects:
//   RegWrite and MemWrite are generated only by the main decoder. PCSrc affects
//   control flow but does not directly alter register or memory write enables.
// -----------------------------------------------------------------------------
// Top-level control path: main decoder, ALU decoder, and branch decision.
module Control_Unit_Top(
    input  wire [6:0] Op,
    input  wire [2:0] funct3,
    input  wire [6:0] funct7,
    input  wire       Zero,
    output wire       RegWrite,
    output wire [1:0] ImmSrc,
    output wire       ALUSrc,
    output wire       MemWrite,
    output wire       ResultSrc,
    output wire       PCSrc,
    output wire [2:0] ALUControl
);

    wire [1:0] ALUOp;
    wire       Branch;

    // Coarse opcode-class decoding.
    Main_Decoder u_main_decoder (
        .Op        (Op),
        .RegWrite  (RegWrite),
        .ImmSrc    (ImmSrc),
        .ALUSrc    (ALUSrc),
        .MemWrite  (MemWrite),
        .ResultSrc (ResultSrc),
        .Branch    (Branch),
        .ALUOp     (ALUOp)
    );

    // Fine ALU-function decoding.
    ALU_Decoder u_alu_decoder (
        .ALUOp      (ALUOp),
        .funct3     (funct3),
        .funct7     (funct7),
        .op         (Op),
        .ALUControl (ALUControl)
    );

    // The implemented branch subset contains BEQ only.
    // Only an equal BEQ may select the branch target.
    assign PCSrc = Branch & Zero & (funct3 == 3'b000);

endmodule

`default_nettype wire
