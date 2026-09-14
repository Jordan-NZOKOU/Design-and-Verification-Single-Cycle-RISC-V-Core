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
 * Testbench: Single_Cycle_Top_tb
 *
 * Verification intent:
 * - run the release-level program across every implemented instruction class;
 * - check eleven register values and two data-memory words;
 * - prove exactly two stores occurred;
 * - detect execution of the address skipped by the taken branch;
 * - confirm branch activity and stabilization in the terminal loop.
 *
 * All executable statements, cycle count, and reference values are preserved
 * across releases. Documentation refinements do not alter the stimulus or
 * acceptance criteria.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Regression scope:
//   The final test combines all supported instruction classes in one dependency
//   chain and checks registers, memory, store count, skipped-PC behavior, branch
//   activity, and terminal-loop stability.
//
// Independence of evidence:
//   End-state checks are complemented by the ROM-image reproduction step and the
//   external Python reference model executed by repository preflight.
//
// Completion model:
//   The test runs a bounded number of cycles long enough to reach and observe the
//   terminal loop. It then evaluates all accumulated architectural evidence.
// -----------------------------------------------------------------------------
// Final self-checking regression for the single-cycle processor. The program
// combines arithmetic, logical, load/store, signed comparison, and BEQ flows.
// The checker validates registers, memory, store count, branch trajectory, and
// terminal-loop stability.
module Single_Cycle_Top_tb;

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
    integer store_count;
    integer taken_branch_count;
    integer skipped_pc_seen;

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
        $dumpfile("single_cycle_top.vcd");
        $dumpvars(0, Single_Cycle_Top_tb);
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
            store_count        = 0;
            taken_branch_count = 0;
            skipped_pc_seen    = 0;
        end
        else begin
            $display("cycle=%0d PC=%h Instr=%h RegWrite=%b rd=%0d Result=%h MemWrite=%b Address=%h WD=%h Zero=%b PCSrc=%b PCTarget=%h",
                     cycle_count, pc, instr, dut.RegWrite, instr[11:7], result,
                     mem_write, alu_result, write_data, dut.Zero, dut.PCSrc,
                     dut.PCTarget);

            if (mem_write)
                store_count = store_count + 1;

            if (dut.PCSrc)
                taken_branch_count = taken_branch_count + 1;

            // PC=0x24 contains addi x12,x0,99 and must be skipped.
            if (pc == 32'h00000024)
                skipped_pc_seen = 1;

            cycle_count = cycle_count + 1;
        end
    end

    initial begin
        clk                = 1'b0;
        rst_n              = 1'b0;
        error_count        = 0;
        cycle_count        = 0;
        store_count        = 0;
        taken_branch_count = 0;
        skipped_pc_seen    = 0;

        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        // The useful program reaches the terminal loop at PC=0x3C. Additional
        // cycles verify that the loop remains stable.
        repeat (22) @(posedge clk);
        #1;

        check_register(5,  32'd5);
        check_register(6,  32'd4);
        check_register(7,  32'd5);
        check_register(8,  32'd4);
        check_register(9,  32'd1);
        check_register(10, 32'd1);
        check_register(11, 32'd5);
        check_register(12, 32'd2);
        check_register(13, 32'hFFFFFFFF);
        check_register(14, 32'd1);
        check_register(15, 32'hFFFFFFFF);

        check_memory(0, 32'd5);
        check_memory(1, 32'd2);

        if (store_count !== 2) begin
            $display("FAIL: data-memory write count=%0d expected=2", store_count);
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: observed exactly two data-memory writes");
        end

        if (skipped_pc_seen != 0) begin
            $display("FAIL: skipped instruction at PC=00000024 was executed");
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: PC=00000024 was not observed");
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

        if (pc !== 32'h0000003C) begin
            $display("FAIL: final PC=%h expected=0000003C", pc);
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: final PC is stable at 0000003C");
        end

        if (error_count == 0) begin
            $display("TEST FINAL PROCESSOR PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST FINAL PROCESSOR FAILED: %0d error(s)", error_count);
        end
    end

endmodule

`default_nettype wire
