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

# Central automation entry point. Every public target delegates to a small,
# reviewable script so the same flow is available locally and in GitHub Actions.
PYTHON ?= python3

.PHONY: help repository-check python-test reference-test assemble assemble-check \
        reference-model diagrams report checksums preflight iverilog test test-vcd \
        test-project questa clean

help:
	@echo "Nexvantis RV32I project targets:"
	@echo "  make preflight      Validate structure, docs, tools, program image, and reference model"
	@echo "  make iverilog       Run all RTL simulations with Icarus Verilog"
	@echo "  make test           Run preflight plus the complete Icarus regression"
	@echo "  make test-vcd       Run all RTL tests and retain VCD waveforms"
	@echo "  make test-project PROJECT=03_alu"
	@echo "  make questa         Run all QuestaSim/ModelSim simulations"
	@echo "  make assemble       Regenerate the final program HEX image"
	@echo "  make diagrams       Regenerate native Draw.io sources and SVG/PNG/PDF exports"
	@echo "  make report         Rebuild the complete English PDF report"
	@echo "  make checksums      Regenerate the release SHA-256 inventory"
	@echo "  make clean          Remove generated simulator and report build artifacts"

repository-check:
	$(PYTHON) scripts/repository_check.py

python-test:
	$(PYTHON) -m unittest discover -s 12_tools -p 'test_*.py' -v

reference-test:
	$(PYTHON) -m unittest discover -s scripts -p 'test_reference_model.py' -v

assemble:
	$(PYTHON) 12_tools/mini_assembler.py \
		12_tools/final_program.asm \
		12_tools/final_program_generated.hex

assemble-check:
	@tmp_file=$$(mktemp); \
	$(PYTHON) 12_tools/mini_assembler.py 12_tools/final_program.asm $$tmp_file >/dev/null; \
	diff -u 11_final_processor/program.hex $$tmp_file; \
	rm -f $$tmp_file; \
	echo "Final program HEX is reproducible."

reference-model:
	$(PYTHON) scripts/reference_model.py

diagrams:
	$(PYTHON) scripts/generate_diagrams.py

report:
	./scripts/build_report.sh

checksums:
	$(PYTHON) scripts/generate_checksums.py

preflight: repository-check python-test reference-test assemble-check reference-model

iverilog:
	$(PYTHON) scripts/run_iverilog.py

test: preflight iverilog

test-vcd: preflight
	$(PYTHON) scripts/run_iverilog.py --vcd

test-project:
	@test -n "$(PROJECT)" || (echo "Set PROJECT, for example PROJECT=03_alu" && exit 2)
	$(PYTHON) scripts/run_iverilog.py --project "$(PROJECT)" --vcd

questa:
	./run_all_linux.sh

clean:
	find . -type d -name build -prune -exec rm -rf {} +
	find . -type d -name work -prune -exec rm -rf {} +
	find . -type f \( -name '*.vcd' -o -name '*.fst' -o -name 'transcript' \
		-o -name 'vsim.wlf' -o -name '*.log' -o -name '*.vvp' \) -delete
	cd 00_documentation/report_source && latexmk -C nexvantis_rv32i_single_cycle_report.tex || true
