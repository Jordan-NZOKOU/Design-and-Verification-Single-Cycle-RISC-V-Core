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
 * Testbench: Integration_Load_Store_tb
 *
 * Verification intent:
 * - execute the load/store integration program;
 * - verify effective addresses, two committed stores, load write-back, and
 *   arithmetic after a load;
 * - check final register and memory state;
 * - count MemWrite pulses so duplicate or missing transactions cannot hide.
 *
 * The complete V4 stimulus and acceptance criteria are preserved.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Integration intent:
//   The workload creates a complete SW -> LW -> arithmetic -> SW dependency
//   chain. Register checks prove load/write-back; memory checks prove stores.
//
// Transaction evidence:
//   Counting MemWrite pulses prevents duplicate stores from being hidden by a
//   final memory value that happens to match the expectation.
//
// Observation policy:
//   Debug ports support cycle-level review; hierarchical arrays are checked only
//   for the final architectural state.
// -----------------------------------------------------------------------------
// Integration test for LW and SW. It checks effective-address generation,
// synchronous stores, asynchronous loads, register write-back, and the exact
// number of data-memory write pulses.
module Integration_Load_Store_tb;

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
        $dumpfile("integration_load_store.vcd");
        $dumpvars(0, Integration_Load_Store_tb);
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
            cycle_count = 0;
            store_count = 0;
        end
        else begin
            $display("cycle=%0d PC=%h Instr=%h RegWrite=%b rd=%0d Result=%h MemWrite=%b Address=%h WD=%h PCSrc=%b",
                     cycle_count, pc, instr, dut.RegWrite, instr[11:7], result,
                     mem_write, alu_result, write_data, dut.PCSrc);

            if (mem_write)
                store_count = store_count + 1;

            cycle_count = cycle_count + 1;
        end
    end

    initial begin
        clk         = 1'b0;
        rst_n       = 1'b0;
        // Initialize deterministic stimulus, counters, and control inputs.
        error_count = 0;
        cycle_count = 0;
        store_count = 0;

        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        repeat (10) @(posedge clk);
        #1;

        check_register(5, 32'd42);
        check_register(6, 32'd42);
        check_register(7, 32'd84);

        check_memory(0, 32'd42);
        check_memory(1, 32'd84);

        if (store_count !== 2) begin
            $display("FAIL: MemWrite pulse count=%0d expected=2", store_count);
            error_count = error_count + 1;
        end
        else begin
            $display("PASS: observed exactly two data-memory writes");
        end

        if (error_count == 0) begin
            $display("TEST LOAD/STORE INTEGRATION PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST LOAD/STORE INTEGRATION FAILED: %0d error(s)",
                   error_count);
        end
    end

endmodule

`default_nettype wire
