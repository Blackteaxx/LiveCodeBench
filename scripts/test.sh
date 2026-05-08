#!/usr/bin/env bash
set -euo pipefail

python task_tester.py \
  --json data/1873_A.json \
  --use_starter_code \
  --timeout "${1:-6}"
