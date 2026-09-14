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
 * Testbench: Control_Unit_Top_tb
 *
 * Verification intent:
 * - check the complete control vector for every supported instruction class;
 * - distinguish ADD from SUB using opcode and funct7;
 * - prove I-type immediate bits cannot be misinterpreted as funct7;
 * - check BEQ taken/not-taken qualification;
 * - suppress unsupported branch types and unknown opcodes safely.
 *
 * Test vectors and expected controls remain identical to Version 4.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Verification matrix:
//   The vectors span every supported instruction class, every ALU operation,
//   both BEQ outcomes, an unsupported branch function, and an unknown opcode.
//
// Packed comparison:
//   All control outputs are concatenated into one comparison so a single vector
//   describes the complete expected control word. The diagnostic then prints
//   fields separately to identify the incorrect control.
//
// Safety proof:
//   The unsupported-opcode vector specifically requires both architectural write
//   enables and PCSrc to remain low.
// -----------------------------------------------------------------------------
// Directed checks for every implemented opcode/funct3/funct7 combination,
// taken/not-taken BEQ behavior, unsupported branch conditions, and unknown
// opcode defaults.
module Control_Unit_Top_tb;

    reg  [6:0] op;
    reg  [2:0] funct3;
    reg  [6:0] funct7;
    reg        zero;

    wire       reg_write;
    wire [1:0] imm_src;
    wire       alu_src;
    wire       mem_write;
    wire       result_src;
    wire       pc_src;
    wire [2:0] alu_control;

    // Accumulates mismatches so all directed cases can run before the final verdict.
    integer error_count;

    Control_Unit_Top dut (
        .Op         (op),
        .funct3     (funct3),
        .funct7     (funct7),
        .Zero       (zero),
        .RegWrite   (reg_write),
        .ImmSrc     (imm_src),
        .ALUSrc     (alu_src),
        .MemWrite   (mem_write),
        .ResultSrc  (result_src),
        .PCSrc      (pc_src),
        .ALUControl (alu_control)
    );

    // Optional waveform export. Simulation scripts define DUMP_VCD only when requested.
`ifdef DUMP_VCD
    // Main directed stimulus and final self-checking verdict.
    initial begin
        $dumpfile("control_unit.vcd");
        $dumpvars(0, Control_Unit_Top_tb);
    end
`endif

    // Compare the complete output-control bundle as a single contract.
    task check_controls;
        input [255:0] test_name;
        input         expected_reg_write;
        input [1:0]   expected_imm_src;
        input         expected_alu_src;
        input         expected_mem_write;
        input         expected_result_src;
        input         expected_pc_src;
        input [2:0]   expected_alu_control;
        begin
            #1;
            if ({reg_write, imm_src, alu_src, mem_write, result_src,
                 pc_src, alu_control}
                !==
                {expected_reg_write, expected_imm_src, expected_alu_src,
                 expected_mem_write, expected_result_src, expected_pc_src,
                 expected_alu_control}) begin
                $display("FAIL %-22s actual=%b_%b_%b_%b_%b_%b_%b expected=%b_%b_%b_%b_%b_%b_%b",
                         test_name,
                         reg_write, imm_src, alu_src, mem_write,
                         result_src, pc_src, alu_control,
                         expected_reg_write, expected_imm_src, expected_alu_src,
                         expected_mem_write, expected_result_src,
                         expected_pc_src, expected_alu_control);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS %-22s RW=%b MW=%b PCSrc=%b ALUControl=%b",
                         test_name, reg_write, mem_write, pc_src, alu_control);
            end
        end
    endtask

    initial begin
        // Initialize deterministic stimulus, counters, and control inputs.
        error_count = 0;
        zero        = 1'b0;
        funct3      = 3'b000;
        funct7      = 7'b0000000;

        op = 7'b0000011; funct3 = 3'b010;
        check_controls("LW", 1, 2'b00, 1, 0, 1, 0, 3'b000);

        op = 7'b0100011; funct3 = 3'b010;
        check_controls("SW", 0, 2'b01, 1, 1, 0, 0, 3'b000);

        op = 7'b0110011; funct3 = 3'b000; funct7 = 7'b0000000;
        check_controls("ADD", 1, 2'b00, 0, 0, 0, 0, 3'b000);

        funct7 = 7'b0100000;
        check_controls("SUB", 1, 2'b00, 0, 0, 0, 0, 3'b001);

        funct3 = 3'b110; funct7 = 7'b0000000;
        check_controls("OR", 1, 2'b00, 0, 0, 0, 0, 3'b011);

        funct3 = 3'b111;
        check_controls("AND", 1, 2'b00, 0, 0, 0, 0, 3'b010);

        funct3 = 3'b010;
        check_controls("SLT", 1, 2'b00, 0, 0, 0, 0, 3'b101);

        // For I-type instructions, funct7 bits are part of the immediate and
        // must not cause ADDI to be decoded as SUB.
        op = 7'b0010011; funct3 = 3'b000; funct7 = 7'b1111111;
        check_controls("ADDI", 1, 2'b00, 1, 0, 0, 0, 3'b000);

        funct3 = 3'b110;
        check_controls("ORI", 1, 2'b00, 1, 0, 0, 0, 3'b011);

        funct3 = 3'b111;
        check_controls("ANDI", 1, 2'b00, 1, 0, 0, 0, 3'b010);

        funct3 = 3'b010;
        check_controls("SLTI", 1, 2'b00, 1, 0, 0, 0, 3'b101);

        op = 7'b1100011; funct3 = 3'b000; funct7 = 7'b0000000; zero = 1'b0;
        check_controls("BEQ not taken", 0, 2'b10, 0, 0, 0, 0, 3'b001);

        zero = 1'b1;
        check_controls("BEQ taken", 0, 2'b10, 0, 0, 0, 1, 3'b001);

        funct3 = 3'b001;
        check_controls("unsupported branch", 0, 2'b10, 0, 0, 0, 0, 3'b001);

        op = 7'b1111111; funct3 = 3'b000; zero = 1'b0;
        check_controls("unsupported opcode", 0, 2'b00, 0, 0, 0, 0, 3'b000);

        if (error_count == 0) begin
            $display("TEST CONTROL UNIT PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST CONTROL UNIT FAILED: %0d error(s)", error_count);
        end
    end

endmodule

`default_nettype wire
