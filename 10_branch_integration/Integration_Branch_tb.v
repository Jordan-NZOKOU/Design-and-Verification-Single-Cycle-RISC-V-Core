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
 * Testbench: Integration_Branch_tb
 *
 * Verification intent:
 * - prove a taken BEQ redirects PC to PC+ImmExt;
 * - detect any visit to the instruction that must be skipped;
 * - verify the branch target's architectural side effects;
 * - count stores and taken branches and confirm terminal-loop behavior.
 *
 * The V4 program, timing, and acceptance criteria are unchanged.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Control-flow evidence:
//   The test records whether a skipped PC appears, counts taken branch decisions,
//   checks the target-side register/memory effect, and confirms terminal PC.
//
// Why multiple observations are required:
//   A wrong branch may still produce the expected final value by coincidence.
//   PC trajectory and side-effect counts make that false positive much harder.
//
// Terminal loop:
//   The final self-branch provides a stable completion state without requiring a
//   halt instruction that is outside the supported subset.
// -----------------------------------------------------------------------------
// Integration test for BEQ. Verification covers both architectural state and
// PC trajectory so that an incorrect branch implementation cannot be hidden by
// a coincidentally correct final register value.
module Integration_Branch_tb;

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
    integer taken_branch_count;
    integer skipped_pc_seen;
    integer store_count;

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
        $dumpfile("integration_branch.vcd");
        $dumpvars(0, Integration_Branch_tb);
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

    // Inspect the behavioral RAM directly from the verification environment.
    task check_memory;
        input integer word_index;
        input [31:0] expected;
        begin
            if (dut.u_data_memory.mem[word_index] !== expected) begin
                $display("FAIL: mem[%0d] actual=%h expected=%h",
                         word_index,
                         dut.u_data_memory.mem[word_index],
                         expected);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS: mem[%0d]=%h",
                         word_index,
                         dut.u_data_memory.mem[word_index]);
            end
        end
    endtask

    // Per-cycle monitor and evidence collection for text logs and final assertions.
    always @(posedge clk) begin
        if (!rst_n) begin
            cycle_count        = 0;
            taken_branch_count = 0;
            skipped_pc_seen    = 0;
            store_count        = 0;
        end
        else begin
            $display("cycle=%0d PC=%h Instr=%h Zero=%b PCSrc=%b PCTarget=%h RegWrite=%b rd=%0d Result=%h MemWrite=%b Address=%h WD=%h",
                     cycle_count, pc, instr, dut.Zero, dut.PCSrc, dut.PCTarget,
                     dut.RegWrite, instr[11:7], result, mem_write, alu_result,
                     write_data);

            if (dut.PCSrc)
                taken_branch_count = taken_branch_count + 1;

            // PC=12 contains the instruction that must be skipped by the BEQ.
            if (pc == 32'd12)
                skipped_pc_seen = 1;

            if (mem_write)
                store_count = store_count + 1;

            cycle_count = cycle_count + 1;
        end
    end

    initial begin
        clk                = 1'b0;
        rst_n              = 1'b0;
        error_count        = 0;
        cycle_count        = 0;
        taken_branch_count = 0;
        skipped_pc_seen    = 0;
        store_count        = 0;

        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        repeat (12) @(posedge clk);
        #1;

        check_register(1, 32'd1);
        check_register(2, 32'd1);
        check_register(3, 32'd7);
        check_memory(0, 32'd7);

        if (skipped_pc_seen != 0) begin
            $display("FAIL: skipped instruction at PC=12 was executed");
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: PC=12 was not observed");
        end

        if (taken_branch_count < 2) begin
            $display("FAIL: only %0d taken branch event(s) observed",
                     taken_branch_count);
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: %0d taken branch event(s) observed",
                     taken_branch_count);
        end

        if (store_count !== 1) begin
            $display("FAIL: data-memory write count=%0d expected=1", store_count);
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: observed exactly one data-memory write");
        end

        if (pc !== 32'd24) begin
            $display("FAIL: final PC=%h expected=00000018", pc);
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: final PC is stable at 24");
        end

        if (error_count == 0) begin
            $display("TEST BRANCH INTEGRATION PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST BRANCH INTEGRATION FAILED: %0d error(s)",
                   error_count);
        end
    end

endmodule

`default_nettype wire
