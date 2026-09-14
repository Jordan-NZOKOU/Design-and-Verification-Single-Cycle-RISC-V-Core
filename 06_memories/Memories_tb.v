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
 * Testbench: Memories_tb
 *
 * Verification intent:
 * - verify reset-time ROM/RAM outputs;
 * - verify $readmemh program loading;
 * - prove byte-address to word-index conversion at addresses 0, 4, and 8;
 * - verify synchronous stores, asynchronous reads, word retention, and WE
 *   suppression.
 *
 * The executable test content is preserved exactly from Version 4.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Verification split:
//   ROM checks prove byte-to-word addressing and reset-visible NOP behavior.
//   RAM checks prove synchronous writes, asynchronous reads, retention, and
//   write-enable suppression.
//
// Address evidence:
//   Consecutive words are deliberately accessed at addresses 0, 4, and 8 so an
//   incorrect direct-byte-index implementation fails immediately.
//
// State observation:
//   Readback is performed through the public RD port; the test does not need to
//   force internal array contents after reset.
// -----------------------------------------------------------------------------
// Joint verification of instruction and data memories: HEX loading,
// asynchronous reads, synchronous writes, reset outputs, and byte-to-word
// address conversion.
module Memories_tb;

    localparam integer CLK_PERIOD_NS = 10;

    reg         clk;
    reg         rst_n;
    reg         we;
    reg  [31:0] addr_instr;
    reg  [31:0] addr_data;
    reg  [31:0] write_data;
    wire [31:0] instr;
    wire [31:0] read_data;

    // Accumulates mismatches so all directed cases can run before the final verdict.
    integer error_count;

    Instruction_Memory #(
        .MEMFILE ("mem_test.hex")
    ) imem (
        .rst_n (rst_n),
        .A     (addr_instr),
        .RD    (instr)
    );

    Data_Memory dmem (
        .clk   (clk),
        .rst_n (rst_n),
        .WE    (we),
        .A     (addr_data),
        .WD    (write_data),
        .RD    (read_data)
    );

    // Free-running clock used only by the verification environment.
    always #(CLK_PERIOD_NS / 2) clk = ~clk;

    // Optional waveform export. Simulation scripts define DUMP_VCD only when requested.
`ifdef DUMP_VCD
    // Main directed stimulus and final self-checking verdict.
    initial begin
        $dumpfile("memories.vcd");
        $dumpvars(0, Memories_tb);
    end
`endif

    // Four-state-aware checker used to reject unknown and high-impedance results.
    task check_value;
        input [31:0] actual;
        input [31:0] expected;
        input [255:0] test_name;
        begin
            #1;
            if (actual !== expected) begin
                $display("FAIL %-30s actual=%h expected=%h", test_name, actual, expected);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS %-30s value=%h", test_name, actual);
            end
        end
    endtask

    initial begin
        clk         = 1'b0;
        rst_n       = 1'b0;
        we          = 1'b0;
        addr_instr  = 32'd0;
        addr_data   = 32'd0;
        write_data  = 32'd0;
        // Initialize deterministic stimulus, counters, and control inputs.
        error_count = 0;

        check_value(instr,     32'h00000013, "ROM output during reset");
        check_value(read_data, 32'd0,        "RAM output during reset");

        @(negedge clk);
        rst_n = 1'b1;

        // Byte addresses 0, 4, and 8 must select consecutive ROM words.
        addr_instr = 32'd0;
        check_value(instr, 32'hDEADBEEF, "ROM byte address 0");
        addr_instr = 32'd4;
        check_value(instr, 32'h12345678, "ROM byte address 4");
        addr_instr = 32'd8;
        check_value(instr, 32'hCAFEBABE, "ROM byte address 8");

        addr_data  = 32'd0;
        write_data = 32'hCAFEBABE;
        we         = 1'b1;
        @(posedge clk);
        @(negedge clk);
        we = 1'b0;
        check_value(read_data, 32'hCAFEBABE, "RAM word index 0");

        addr_data  = 32'd4;
        write_data = 32'h0BADF00D;
        we         = 1'b1;
        @(posedge clk);
        @(negedge clk);
        we = 1'b0;
        check_value(read_data, 32'h0BADF00D, "RAM word index 1");

        addr_data = 32'd0;
        check_value(read_data, 32'hCAFEBABE, "RAM word 0 retained");

        write_data = 32'hFFFFFFFF;
        we         = 1'b0;
        @(posedge clk);
        check_value(read_data, 32'hCAFEBABE, "WE low blocks write");

        if (error_count == 0) begin
            $display("TEST MEMORIES PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST MEMORIES FAILED: %0d error(s)", error_count);
        end
    end

endmodule

`default_nettype wire
