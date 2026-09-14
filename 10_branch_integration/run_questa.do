# Copyright 2026 Jordan Nzokou and Doeg Tiozang
# Project: Nexvantis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# QuestaSim/ModelSim batch flow for: BEQ Branch and Next-PC Integration
#
# Launch from any working directory with:
#     vsim -c -do 10_branch_integration/run_questa.do
#
# The testbench is self-checking. A successful run reaches $finish and exits
# with status 0. Any compile failure, Tcl error, or Verilog $fatal exits with a
# non-zero status so the script can be used directly from CI.

transcript on
onerror {quit -code 1 -force}
onbreak {quit -code 1 -force}

# Resolve paths from the script itself, not from the caller. This is important
# because the same file is used both directly and by the root regression script.
set SCRIPT_DIR [file dirname [file normalize [info script]]]
cd $SCRIPT_DIR

# Remove any stale compiled library. Recreating the library on every run avoids
# accidental success caused by an old module that is no longer in the source set.
if {[file exists work]} {
    vdel -lib work -all
}
vlib work
vmap work work

# Compile sources in dependency order. This list mirrors project_manifest.json,
# which is also consumed by the Icarus regression driver.
set SOURCES {
    Mux.v
    PC.v
    PC_Adder.v
    ALU.v
    Register_File.v
    Sign_Extend.v
    Instruction_Memory.v
    Data_Memory.v
    Main_Decoder.v
    ALU_Decoder.v
    Control_Unit_Top.v
    Single_Cycle_Top.v
    Integration_Branch_tb.v
}
foreach source $SOURCES {
    puts "Compiling $source"
    vlog -sv -work work $source
}

# +acc preserves hierarchical visibility for waveform inspection and any
# deliberate white-box checks performed by the testbench.
vsim -voptargs=+acc work.Integration_Branch_tb

# Keep the native simulator wave database useful during an interactive rerun.
add wave -r /*

# Export the complete testbench hierarchy to a portable VCD file. GTKWave can
# open this artifact without requiring the proprietary simulator database.
vcd file integration_branch.vcd
vcd add -r /Integration_Branch_tb/*

# The self-checking testbench owns the stopping condition and final verdict.
run -all
vcd flush
vcd off
quit -code 0 -force
