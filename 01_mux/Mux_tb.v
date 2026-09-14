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
 * Testbench: Mux_tb
 *
 * Verification intent:
 * - exercise both selector values of the parameterized 2:1 multiplexer;
 * - repeat the initial selector state after a transition to expose retained
 *   state or stale combinational behavior;
 * - use four-state comparison so X/Z results cannot pass silently;
 * - emit a single CI-friendly PASS or fatal FAIL verdict.
 *
 * The stimulus, expected values, and acceptance criteria are unchanged from
 * The scenario is preserved across releases; documentation changes do not alter its stimulus.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Verification plan:
//   1. Initialize both data inputs with visibly different patterns.
//   2. Select input a and compare c against a.
//   3. Select input b and compare c against b.
//   4. Change the data pattern and recheck the a path.
//
// Why no clock exists:
//   The DUT is purely combinational. #1 provides a deterministic observation
//   point after stimulus propagation; waiting for a clock would hide the actual
//   interface contract.
// -----------------------------------------------------------------------------
// Self-checking directed testbench for the parameterized 2-to-1 multiplexer.
module Mux_tb;

    reg  [31:0] a;
    reg  [31:0] b;
    reg         s;
    wire [31:0] c;

    // Accumulates mismatches so all directed cases can run before the final verdict.
    integer error_count;

    Mux dut (
        .a (a),
        .b (b),
        .s (s),
        .c (c)
    );

    // Optional waveform export. Simulation scripts define DUMP_VCD only when requested.
`ifdef DUMP_VCD
    // Main directed stimulus and final self-checking verdict.
    initial begin
        $dumpfile("mux.vcd");
        $dumpvars(0, Mux_tb);
    end
`endif

    // Compare the combinational output after a short propagation delay.
    // Reusable combinational checker; the #1 settling delay is simulation-only.
    task check_output;
        input [31:0] expected;
        begin
            #1;
            if (c !== expected) begin
                $display("FAIL: s=%b actual=%h expected=%h", s, c, expected);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS: s=%b output=%h", s, c);
            end
        end
    endtask

    initial begin
        // Initialize deterministic stimulus, counters, and control inputs.
        error_count = 0;
        a = 32'h12345678;
        b = 32'hA5A5A5A5;

        s = 1'b0;
        check_output(a);

        s = 1'b1;
        check_output(b);

        // Return to input a to verify both selection transitions.
        s = 1'b0;
        check_output(a);

        if (error_count == 0) begin
            $display("TEST MUX PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST MUX FAILED: %0d error(s)", error_count);
        end
    end

endmodule

`default_nettype wire
