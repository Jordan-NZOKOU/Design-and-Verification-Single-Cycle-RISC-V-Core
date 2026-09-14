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
 * Module: Sign_Extend
 *  *
 *  * Reconstructs and sign-extends I-, S-, and B-type immediates from a 32-bit
 *  * instruction. B-type fields are non-contiguous and include an implicit zero in
 *  * bit 0 because branch displacements are encoded in two-byte units.
 *  *
 *  * ImmSrc: 00=I, 01=S, 10=B. Unsupported selectors return zero.
 */

// -----------------------------------------------------------------------------
// DETAILED ENGINEERING COMMENTARY
//
// ISA mapping:
//   I-type immediates are contiguous. S-type immediates are split around rd-like
//   bits. B-type immediates are split, reordered, and gain an implicit zero bit.
//
// Sign extension:
//   In[31] is the sign bit for all three supported immediate formats. Replication
//   fills the upper destination bits without changing the reconstructed low bits.
//
// Branch alignment:
//   Appending 1'b0 creates the byte displacement consumed directly by PC_Adder.
//   No additional left shift is performed elsewhere in the branch path.
//
// Unsupported selection:
//   A zero default is benign and prevents retention of a previous immediate.
// -----------------------------------------------------------------------------
// RISC-V immediate decoder and sign extender.
// ImmSrc encoding: 2'b00=I-type, 2'b01=S-type, 2'b10=B-type.
module Sign_Extend(
    input  wire [31:0] In,
    input  wire [1:0]  ImmSrc,
    output reg  [31:0] Imm_Ext
);

    // Complete combinational decode of the currently selected immediate format.
    always @(*) begin
        case (ImmSrc)
            // I-type immediate: contiguous instruction bits [31:20].
            2'b00: Imm_Ext = {{20{In[31]}}, In[31:20]};
            // S-type immediate: concatenate high and low fragments.
            2'b01: Imm_Ext = {{20{In[31]}}, In[31:25], In[11:7]};
            // B-type immediate: reorder split fields and append implicit bit 0.
            2'b10: Imm_Ext = {{19{In[31]}}, In[31], In[7],
                              In[30:25], In[11:8], 1'b0};
            default: Imm_Ext = 32'b0;
        endcase
    end

endmodule

`default_nettype wire
