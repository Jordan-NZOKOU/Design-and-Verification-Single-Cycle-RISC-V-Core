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
 * Module: Single_Cycle_Top
 *  *
 *  * Structural top level for the implemented RV32I single-cycle subset. It wires
 *  * fetch, decode, execute, memory, write-back, and next-PC selection without
 *  * introducing pipeline state. Each instruction completes within one clock
 *  * period and commits at the next rising edge.
 *  *
 *  * Supported instructions: ADD, SUB, AND, OR, SLT, ADDI, ANDI, ORI, SLTI, LW,
 *  * SW, and BEQ. Debug outputs are observation-only and do not affect state.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Microarchitectural boundary:
//   The module is structural. It introduces no pipeline state and does not
//   reimplement sub-block behavior. The longest supported instruction traverses
//   the complete combinational datapath before the next rising edge.
//
// Signal organization:
//   PC/PCNext/PCPlus4/PCTarget form the control-flow path. RD1/RD2/ImmExt/SrcB
//   form operand selection. ALUResult/ReadData/Result form memory/write-back.
//
// Commit points:
//   The PC, register file, and data memory are the only architectural state
//   owners. Their writes occur on the rising edge under their local enables.
//
// Debug policy:
//   Debug outputs are direct observation taps. They never feed control or data
//   back into the processor, so verification visibility cannot change behavior.
//
// Parameterization:
//   MEMFILE binds instruction memory to the program local to each milestone,
//   keeping integration directories independently runnable.
// -----------------------------------------------------------------------------
// Single-cycle RV32I subset processor.
// Supported instructions: ADD, SUB, AND, OR, SLT, ADDI, ANDI, ORI, SLTI,
// LW, SW, and BEQ. Debug outputs are observation-only ports for verification.
module Single_Cycle_Top #(
    parameter MEMFILE = "program.hex"
)(
    input  wire        clk,
    input  wire        rst_n,
    output wire [31:0] PC_Debug,
    output wire [31:0] Instr_Debug,
    output wire        MemWrite_Debug,
    output wire [31:0] ALUResult_Debug,
    output wire [31:0] WriteData_Debug,
    output wire [31:0] Result_Debug
);

    // Datapath signals: addresses, operands, immediate, memory data, and write-back.
    wire [31:0] PC;
    wire [31:0] PCNext;
    wire [31:0] PCPlus4;
    wire [31:0] PCTarget;
    wire [31:0] Instr;
    wire [31:0] RD1;
    wire [31:0] RD2;
    wire [31:0] ImmExt;
    wire [31:0] SrcB;
    wire [31:0] ALUResult;
    wire [31:0] ReadData;
    wire [31:0] Result;

    // Control signals generated from the current instruction and ALU Zero flag.
    wire       RegWrite;
    wire [1:0] ImmSrc;
    wire       ALUSrc;
    wire       MemWrite;
    wire       ResultSrc;
    wire       PCSrc;
    wire [2:0] ALUControl;
    wire       Zero;

    // Sequential control-flow state.
    PC_Module u_pc (
        .clk     (clk),
        .rst_n   (rst_n),
        .PC_Next (PCNext),
        .PC      (PC)
    );

    // Fixed-width instructions advance the sequential path by four bytes.
    PC_Adder u_adder_pc_plus_4 (
        .a (PC),
        .b (32'd4),
        .c (PCPlus4)
    );

    // Branch targets are PC-relative in the implemented BEQ path.
    PC_Adder u_adder_pc_target (
        .a (PC),
        .b (ImmExt),
        .c (PCTarget)
    );

    // Choose PC+4 unless the qualified branch decision asserts PCSrc.
    Mux u_mux_pc (
        .a (PCPlus4),
        .b (PCTarget),
        .s (PCSrc),
        .c (PCNext)
    );

    // Instruction fetch from the current byte address.
    Instruction_Memory #(
        .MEMFILE (MEMFILE)
    ) u_instruction_memory (
        .rst_n (rst_n),
        .A     (PC),
        .RD    (Instr)
    );

    // Decode rs1, rs2, and rd fields and commit write-back at the clock edge.
    Register_File u_register_file (
        .clk   (clk),
        .rst_n (rst_n),
        .WE3   (RegWrite),
        .A1    (Instr[19:15]),
        .A2    (Instr[24:20]),
        .A3    (Instr[11:7]),
        .WD3   (Result),
        .RD1   (RD1),
        .RD2   (RD2)
    );

    // Reconstruct the instruction-format-specific immediate.
    Sign_Extend u_sign_extend (
        .In      (Instr),
        .ImmSrc  (ImmSrc),
        .Imm_Ext (ImmExt)
    );

    // Select register operand or immediate for ALU input B.
    Mux u_mux_src_b (
        .a (RD2),
        .b (ImmExt),
        .s (ALUSrc),
        .c (SrcB)
    );

    // Execute arithmetic/logic, address generation, or BEQ comparison.
    ALU u_alu (
        .A          (RD1),
        .B          (SrcB),
        .ALUControl (ALUControl),
        .Result     (ALUResult),
        .OverFlow   (),
        .Carry      (),
        .Zero       (Zero),
        .Negative   ()
    );

    // Generate all datapath controls and the final branch decision.
    Control_Unit_Top u_control_unit (
        .Op         (Instr[6:0]),
        .funct3     (Instr[14:12]),
        .funct7     (Instr[31:25]),
        .Zero       (Zero),
        .RegWrite   (RegWrite),
        .ImmSrc     (ImmSrc),
        .ALUSrc     (ALUSrc),
        .MemWrite   (MemWrite),
        .ResultSrc  (ResultSrc),
        .PCSrc      (PCSrc),
        .ALUControl (ALUControl)
    );

    // Complete aligned word loads/stores through the ALU-generated address.
    Data_Memory u_data_memory (
        .clk   (clk),
        .rst_n (rst_n),
        .WE    (MemWrite),
        .A     (ALUResult),
        .WD    (RD2),
        .RD    (ReadData)
    );

    // Select ALU or memory data for architectural register write-back.
    Mux u_mux_result (
        .a (ALUResult),
        .b (ReadData),
        .s (ResultSrc),
        .c (Result)
    );

    // Observation-only ports consumed by integration testbenches.
    assign PC_Debug        = PC;
    assign Instr_Debug     = Instr;
    assign MemWrite_Debug  = MemWrite;
    assign ALUResult_Debug = ALUResult;
    assign WriteData_Debug = RD2;
    assign Result_Debug    = Result;

endmodule

`default_nettype wire
