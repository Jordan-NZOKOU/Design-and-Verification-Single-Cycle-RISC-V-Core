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
 * Testbench: Integration_ALU_tb
 *
 * Verification intent:
 * - execute the arithmetic-only integration program;
 * - check six architectural destination registers;
 * - prove that no data-memory write is generated;
 * - log each cycle for CI diagnostics and waveform correlation.
 *
 * Program duration, checks, and expected state are unchanged from Version 4.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Integration intent:
//   This test verifies instruction fetch, decode, register addressing, immediate
//   selection, ALU execution, and write-back across a program, while requiring
//   that the unused data-memory write path remains inactive.
//
// End-state strategy:
//   Register values summarize multiple dependent instructions. MemWrite pulse
//   counting adds a negative side-effect check that final registers alone cannot
//   provide.
// -----------------------------------------------------------------------------
// Integration test for the arithmetic datapath. The program exercises ADDI,
// OR, AND, SUB, and SLT and must not generate any data-memory write.
module Integration_ALU_tb;

    localparam integer CLK_PERIOD_NS = 10;

    reg         clk;
    reg         rst_n;
    wire [31:0] pc;
    wire [31:0] instr;
    wire        mem_write;
    wire [31:0] alu_result;
    wire [31:0] write_data;
    wire [31:0] result;

    // Accumulates mismatches so all directed cases can run before the final verdict.
    integer error_count;
    integer cycle_count;
    integer memwrite_count;

    Single_Cycle_Top #(
        .MEMFILE ("program.hex")
    ) dut (
        .clk             (clk),
        .rst_n           (rst_n),
        .PC_Debug        (pc),
        .Instr_Debug     (instr),
        .MemWrite_Debug  (mem_write),
        .ALUResult_Debug (alu_result),
        .WriteData_Debug (write_data),
        .Result_Debug    (result)
    );

    // Free-running clock used only by the verification environment.
    always #(CLK_PERIOD_NS / 2) clk = ~clk;

    // Optional waveform export. Simulation scripts define DUMP_VCD only when requested.
`ifdef DUMP_VCD
    // Main directed stimulus and final self-checking verdict.
    initial begin
        $dumpfile("integration_alu.vcd");
        $dumpvars(0, Integration_ALU_tb);
    end
`endif

    // Read architectural state hierarchically after the program has completed.
    task check_register;
        input [4:0]  register_index;
        input [31:0] expected;
        begin
            if (dut.u_register_file.registers[register_index] !== expected) begin
                $display("FAIL: x%0d actual=%h expected=%h",
                         register_index,
                         dut.u_register_file.registers[register_index],
                         expected);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS: x%0d=%h",
                         register_index,
                         dut.u_register_file.registers[register_index]);
            end
        end
    endtask

    // Text trace complements the VCD and makes CI failures easy to diagnose.
    // Per-cycle monitor and evidence collection for text logs and final assertions.
    always @(posedge clk) begin
        if (!rst_n) begin
            cycle_count    = 0;
            memwrite_count = 0;
        end
        else begin
            $display("cycle=%0d PC=%h Instr=%h RegWrite=%b rd=%0d Result=%h MemWrite=%b ALU=%h WD=%h PCSrc=%b",
                     cycle_count, pc, instr, dut.RegWrite, instr[11:7], result,
                     mem_write, alu_result, write_data, dut.PCSrc);

            if (mem_write)
                memwrite_count = memwrite_count + 1;

            cycle_count = cycle_count + 1;
        end
    end

    initial begin
        // Initialize deterministic stimulus, counters, and control inputs.
        clk            = 1'b0;
        rst_n          = 1'b0;
        error_count    = 0;
        cycle_count    = 0;
        memwrite_count = 0;

        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        repeat (10) @(posedge clk);
        #1;

        check_register(5,  32'd5);
        check_register(6,  32'd4);
        check_register(7,  32'd5);
        check_register(8,  32'd4);
        check_register(9,  32'd1);
        check_register(10, 32'd1);

        if (memwrite_count !== 0) begin
            $display("FAIL: unexpected MemWrite pulses=%0d", memwrite_count);
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: no unexpected data-memory writes");
        end

        if (error_count == 0) begin
            $display("TEST ALU AND REGISTER INTEGRATION PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST ALU AND REGISTER INTEGRATION FAILED: %0d error(s)",
                   error_count);
        end
    end

endmodule

`default_nettype wire
