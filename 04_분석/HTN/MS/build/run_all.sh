#!/bin/bash
# run_all.sh — figures, manuscript, and Supplemental Material from the result tables.
set -e; cd "$(dirname "$0")"
python3 figs_htn.py
python3 build_ms_htn.py
python3 esm_htn.py
