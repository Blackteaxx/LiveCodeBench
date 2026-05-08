#!/usr/bin/env bash
set -euo pipefail

HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}" \
HF_HOME="${HF_HOME:-./hf-cache}" \
python save_json.py \
  --scenario codegeneration \
  --release_version "${1:-release_v6}" \
  --per_record_dir "${2:-./data}"
