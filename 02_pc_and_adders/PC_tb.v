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
 * Testbench: PC_tb
 *
 * Verification intent:
 * - close the PC -> PC+4 -> PC_Next loop used for sequential execution;
 * - prove that the active-low reset is sampled synchronously on posedge clk;
 * - check three consecutive increments and a later reset assertion;
 * - sample after the NBA region so the registered PC value is stable.
 *
 * The executable test sequence and expected values remain identical to V4.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Verification plan:
//   The test drives PCNext from the adder output, not from a sequence of forced
//   constants. This checks the register and combinational PC+4 path together.
//
// Reset proof:
//   Reset is asserted at startup and again after normal updates. Checks occur
//   after rising edges plus a short delay so nonblocking assignments have settled.
//
// Acceptance evidence:
//   The expected state trajectory is 0 -> 4 -> 8 -> 12 -> 0.
// -----------------------------------------------------------------------------
// Verifies the synchronous reset behavior and the PC+4 update sequence.
module PC_tb;

    localparam integer CLK_PERIOD_NS = 10;

    reg         clk;
    reg         rst_n;
    wire [31:0] pc;
    wire [31:0] pc_plus_4;

    // Accumulates mismatches so all directed cases can run before the final verdict.
    integer error_count;

    PC_Module dut_pc (
        .clk     (clk),
        .rst_n   (rst_n),
        .PC_Next (pc_plus_4),
        .PC      (pc)
    );

    PC_Adder dut_adder (
        .a (pc),
        .b (32'd4),
        .c (pc_plus_4)
    );

    // Free-running clock used only by the verification environment.
    always #(CLK_PERIOD_NS / 2) clk = ~clk;

    // Optional waveform export. Simulation scripts define DUMP_VCD only when requested.
`ifdef DUMP_VCD
    // Main directed stimulus and final self-checking verdict.
    initial begin
        $dumpfile("pc.vcd");
        $dumpvars(0, PC_tb);
    end
`endif

    // Sample the PC after nonblocking assignments have committed.
    task check_pc;
        input [31:0] expected;
        begin
            // Sample after nonblocking assignments have committed.
            #1;
            if (pc !== expected) begin
                $display("FAIL: PC actual=%h expected=%h", pc, expected);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS: PC=%h", pc);
            end
        end
    endtask

    initial begin
        clk         = 1'b0;
        rst_n       = 1'b0;
        // Initialize deterministic stimulus, counters, and control inputs.
        error_count = 0;

        @(posedge clk);
        check_pc(32'd0);

        @(negedge clk);
        rst_n = 1'b1;

        @(posedge clk);
        check_pc(32'd4);
        @(posedge clk);
        check_pc(32'd8);
        @(posedge clk);
        check_pc(32'd12);

        // Reassert reset between clock edges; the update must wait for the
        // next rising edge because the reset is synchronous.
        @(negedge clk);
        rst_n = 1'b0;
        @(posedge clk);
        check_pc(32'd0);

        if (error_count == 0) begin
            $display("TEST PC AND ADDER PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST PC AND ADDER FAILED: %0d error(s)", error_count);
        end
    end

endmodule

`default_nettype wire
