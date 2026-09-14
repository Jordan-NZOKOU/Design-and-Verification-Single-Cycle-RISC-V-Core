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
 * Testbench: Register_File_tb
 *
 * Verification intent:
 * - confirm deterministic reset state;
 * - verify rising-edge writes and independent asynchronous read ports;
 * - prove that WE3 gates updates;
 * - enforce the architectural x0 invariant;
 * - confirm that a later reset clears previously written registers.
 *
 * The stimulus ordering, hierarchical observations, and expected values are
 * unchanged from Version 4.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Verification phases:
//   reset -> write x5 -> write x6 -> dual read -> disabled write -> x0 write
//   attempt -> second reset. The order proves retention and independence.
//
// Edge discipline:
//   Write controls are established before a rising edge. State is inspected
//   after a short delay so the test observes completed nonblocking assignments.
//
// Architectural proof:
//   The x0 check is not merely an initialization check; it actively attempts a
//   nonzero write and verifies the read path still returns zero.
// -----------------------------------------------------------------------------
// Verifies dual asynchronous reads, synchronous writes, write-enable gating,
// reset behavior, and the architectural x0 invariant.
module Register_File_tb;

    localparam integer CLK_PERIOD_NS = 10;

    reg         clk;
    reg         rst_n;
    reg         we3;
    reg  [4:0]  a1;
    reg  [4:0]  a2;
    reg  [4:0]  a3;
    reg  [31:0] wd3;
    wire [31:0] rd1;
    wire [31:0] rd2;

    // Accumulates mismatches so all directed cases can run before the final verdict.
    integer error_count;

    Register_File dut (
        .clk   (clk),
        .rst_n (rst_n),
        .WE3   (we3),
        .A1    (a1),
        .A2    (a2),
        .A3    (a3),
        .WD3   (wd3),
        .RD1   (rd1),
        .RD2   (rd2)
    );

    // Free-running clock used only by the verification environment.
    always #(CLK_PERIOD_NS / 2) clk = ~clk;

    // Optional waveform export. Simulation scripts define DUMP_VCD only when requested.
`ifdef DUMP_VCD
    // Main directed stimulus and final self-checking verdict.
    initial begin
        $dumpfile("register_file.vcd");
        $dumpvars(0, Register_File_tb);
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
                $display("FAIL %-28s actual=%h expected=%h", test_name, actual, expected);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS %-28s value=%h", test_name, actual);
            end
        end
    endtask

    initial begin
        clk         = 1'b0;
        rst_n       = 1'b0;
        we3         = 1'b0;
        a1          = 5'd0;
        a2          = 5'd0;
        a3          = 5'd0;
        wd3         = 32'd0;
        // Initialize deterministic stimulus, counters, and control inputs.
        error_count = 0;

        @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        a1 = 5'd5;
        a2 = 5'd6;
        check_value(rd1, 32'd0, "x5 after reset");
        check_value(rd2, 32'd0, "x6 after reset");

        // Synchronous write to x5.
        a3  = 5'd5;
        wd3 = 32'h12345678;
        we3 = 1'b1;
        @(posedge clk);
        @(negedge clk);
        we3 = 1'b0;
        a1  = 5'd5;
        check_value(rd1, 32'h12345678, "read x5 on RD1");

        // Independent write to x6 followed by simultaneous dual-port reads.
        a3  = 5'd6;
        wd3 = 32'hCAFEBABE;
        we3 = 1'b1;
        @(posedge clk);
        @(negedge clk);
        we3 = 1'b0;
        a1  = 5'd5;
        a2  = 5'd6;
        check_value(rd1, 32'h12345678, "x5 on RD1");
        check_value(rd2, 32'hCAFEBABE, "x6 on RD2");

        // WE3 low must preserve the previous contents.
        a3  = 5'd5;
        wd3 = 32'hDEADBEEF;
        we3 = 1'b0;
        @(posedge clk);
        a1 = 5'd5;
        check_value(rd1, 32'h12345678, "WE3 low preserves x5");

        // Writes to x0 are architecturally discarded.
        @(negedge clk);
        a3  = 5'd0;
        wd3 = 32'hFFFFFFFF;
        we3 = 1'b1;
        @(posedge clk);
        @(negedge clk);
        we3 = 1'b0;
        a1  = 5'd0;
        check_value(rd1, 32'd0, "x0 remains zero");

        // Reassert reset and confirm previously written registers are cleared.
        rst_n = 1'b0;
        @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        a1 = 5'd5;
        a2 = 5'd6;
        check_value(rd1, 32'd0, "x5 cleared by reset");
        check_value(rd2, 32'd0, "x6 cleared by reset");

        if (error_count == 0) begin
            $display("TEST REGISTER FILE PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST REGISTER FILE FAILED: %0d error(s)", error_count);
        end
    end

endmodule

`default_nettype wire
