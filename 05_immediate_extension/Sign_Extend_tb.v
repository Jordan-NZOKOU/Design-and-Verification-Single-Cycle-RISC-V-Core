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
 * Testbench: Sign_Extend_tb
 *
 * Verification intent:
 * - verify positive and negative I-type immediates;
 * - verify split S-type immediate reconstruction;
 * - verify non-contiguous B-type reconstruction and the implicit low zero;
 * - verify the safe default for unsupported ImmSrc values.
 *
 * Every instruction word is a concrete RV32I encoding. The vectors and checks
 * are unchanged from Version 4.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// Vector selection:
//   Each immediate format is tested with one positive and one negative value.
//   Machine words correspond to readable RISC-V instructions documented inline.
//
// Failure localization:
//   Positive cases expose field placement; negative cases additionally expose
//   sign replication. B-type cases also expose the implicit low-zero rule.
//
// Default behavior:
//   An unsupported ImmSrc value must return zero rather than retain a prior case.
// -----------------------------------------------------------------------------
// Covers positive and negative I-, S-, and B-type immediates, including the
// non-contiguous B-type encoding and the unsupported ImmSrc default path.
module Sign_Extend_tb;

    reg  [31:0] instr;
    reg  [1:0]  imm_src;
    wire [31:0] imm_ext;

    // Accumulates mismatches so all directed cases can run before the final verdict.
    integer error_count;

    Sign_Extend dut (
        .In      (instr),
        .ImmSrc  (imm_src),
        .Imm_Ext (imm_ext)
    );

    // Optional waveform export. Simulation scripts define DUMP_VCD only when requested.
`ifdef DUMP_VCD
    // Main directed stimulus and final self-checking verdict.
    initial begin
        $dumpfile("sign_extend.vcd");
        $dumpvars(0, Sign_Extend_tb);
    end
`endif

    // Compare one reconstructed immediate after combinational settling.
    task check_immediate;
        input [31:0] expected;
        input [255:0] test_name;
        begin
            #1;
            if (imm_ext !== expected) begin
                $display("FAIL %-28s actual=%h expected=%h", test_name, imm_ext, expected);
                error_count = error_count + 1;
            end
            else begin
                $display("PASS %-28s immediate=%h", test_name, imm_ext);
            end
        end
    endtask

    initial begin
        // Initialize deterministic stimulus, counters, and control inputs.
        error_count = 0;

        instr   = 32'h00500093; // addi x1, x0, +5
        imm_src = 2'b00;
        check_immediate(32'd5, "I-type +5");

        instr   = 32'hFFC00093; // addi x1, x0, -4
        imm_src = 2'b00;
        check_immediate(32'hFFFFFFFC, "I-type -4");

        instr   = 32'h0020A423; // sw x2, +8(x1)
        imm_src = 2'b01;
        check_immediate(32'd8, "S-type +8");

        instr   = 32'hFE20AC23; // sw x2, -8(x1)
        imm_src = 2'b01;
        check_immediate(32'hFFFFFFF8, "S-type -8");

        instr   = 32'h00208663; // beq x1, x2, +12
        imm_src = 2'b10;
        check_immediate(32'd12, "B-type +12");

        instr   = 32'hFE208CE3; // beq x1, x2, -8
        imm_src = 2'b10;
        check_immediate(32'hFFFFFFF8, "B-type -8");

        instr   = 32'hFFFFFFFF;
        imm_src = 2'b11;
        check_immediate(32'd0, "unsupported ImmSrc");

        if (error_count == 0) begin
            $display("TEST SIGN EXTEND PASSED");
            $finish;
        end
        else begin
            $fatal(1, "TEST SIGN EXTEND FAILED: %0d error(s)", error_count);
        end
    end

endmodule

`default_nettype wire
