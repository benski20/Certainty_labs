#!/usr/bin/env bash
#
# Certainty Labs -- Kaggle Remote GPU Training
#
# Uploads training data, pushes notebook, polls for completion,
# and downloads the trained model back locally.
#
# Usage:
#   ./scripts/kaggle_run.sh <kaggle-username>
#
# Prerequisites:
#   1. pip install kaggle
#   2. Place API token at ~/.kaggle/kaggle.json (chmod 600)
#   3. Training data in demo_dataset/*.jsonl
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Use the Python 3.12 venv with kaggle 2.0 (supports KGAT_ tokens)
KAGGLE_VENV="${PROJECT_DIR}/.kaggle-venv"
if [ -x "${KAGGLE_VENV}/bin/kaggle" ]; then
    KAGGLE="${KAGGLE_VENV}/bin/kaggle"
elif command -v kaggle &> /dev/null; then
    KAGGLE="kaggle"
else
    echo "ERROR: kaggle CLI not found."
    echo "  Run: uv venv .kaggle-venv --python 3.12 && uv pip install kaggle --python .kaggle-venv/bin/python"
    exit 1
fi

# ── Parse username ──────────────────────────────────────────────────
if [ $# -lt 1 ]; then
    echo "Usage: $0 <kaggle-username>"
    echo ""
    echo "Example: $0 benslivinski"
    echo ""
    echo "To find your username, run: python3 -m kaggle config view"
    exit 1
fi

USERNAME="$1"
DATASET_SLUG="${USERNAME}/certainty-eorm-data"
KERNEL_SLUG="${USERNAME}/certainty-labs-eorm-training"

echo "============================================"
echo "  Certainty Labs -- Kaggle Remote Training"
echo "============================================"
echo "Username:  ${USERNAME}"
echo "Dataset:   ${DATASET_SLUG}"
echo "Kernel:    ${KERNEL_SLUG}"
echo ""

# ── Verify kaggle credentials ──────────────────────────────────────
if ! $KAGGLE config view > /dev/null 2>&1; then
    echo "ERROR: Kaggle API not configured."
    echo "  1. Go to https://www.kaggle.com/settings"
    echo "  2. Click 'Create New Token' to download kaggle.json"
    echo "  3. Place it at ~/.kaggle/kaggle.json"
    echo "  4. Run: chmod 600 ~/.kaggle/kaggle.json"
    exit 1
fi
echo "Kaggle credentials OK"
echo ""

# ── Step 1: Upload dataset ─────────────────────────────────────────
echo "── Step 1: Uploading training data as Kaggle Dataset ──"

DATASET_DIR="${PROJECT_DIR}/demo_dataset"
METADATA="${DATASET_DIR}/dataset-metadata.json"

# Patch username into metadata
if grep -q "KAGGLE_USERNAME" "$METADATA"; then
    if [[ "$(uname)" == "Darwin" ]]; then
        sed -i '' "s/KAGGLE_USERNAME/${USERNAME}/g" "$METADATA"
    else
        sed -i "s/KAGGLE_USERNAME/${USERNAME}/g" "$METADATA"
    fi
    echo "Patched username into dataset-metadata.json"
fi

# Check if dataset already exists
if $KAGGLE datasets status "$DATASET_SLUG" > /dev/null 2>&1; then
    echo "Dataset exists, creating new version..."
    $KAGGLE datasets version -p "$DATASET_DIR" -m "Updated data" --dir-mode skip
else
    echo "Creating new dataset..."
    $KAGGLE datasets create -p "$DATASET_DIR"
fi

echo "Dataset upload complete."
echo ""

# Wait for dataset to be ready
echo "Waiting for dataset to be processed (30s)..."
sleep 30

# ── Step 2: Push notebook ──────────────────────────────────────────
echo "── Step 2: Pushing notebook for GPU execution ──"

NOTEBOOK_DIR="${PROJECT_DIR}/notebooks"
KERNEL_META="${NOTEBOOK_DIR}/kernel-metadata.json"

# Patch username into kernel metadata
if grep -q "KAGGLE_USERNAME" "$KERNEL_META"; then
    if [[ "$(uname)" == "Darwin" ]]; then
        sed -i '' "s/KAGGLE_USERNAME/${USERNAME}/g" "$KERNEL_META"
    else
        sed -i "s/KAGGLE_USERNAME/${USERNAME}/g" "$KERNEL_META"
    fi
    echo "Patched username into kernel-metadata.json"
fi

$KAGGLE kernels push -p "$NOTEBOOK_DIR"
echo "Notebook pushed. GPU execution started."
echo ""

# ── Step 3: Poll for completion ────────────────────────────────────
echo "── Step 3: Polling for completion ──"

POLL_INTERVAL=30
MAX_POLLS=120  # 60 minutes max

for i in $(seq 1 $MAX_POLLS); do
    STATUS=$($KAGGLE kernels status "$KERNEL_SLUG" 2>&1 || echo "error")

    if echo "$STATUS" | grep -qi "complete"; then
        echo ""
        echo "Notebook execution COMPLETE."
        break
    elif echo "$STATUS" | grep -qi "error\|cancel"; then
        echo ""
        echo "ERROR: Notebook execution failed."
        echo "$STATUS"
        echo ""
        echo "Check logs: https://www.kaggle.com/code/${KERNEL_SLUG}"
        exit 1
    else
        ELAPSED=$((i * POLL_INTERVAL))
        printf "\r  [%dm %ds] Status: running..." $((ELAPSED/60)) $((ELAPSED%60))
        sleep $POLL_INTERVAL
    fi
done

echo ""

# ── Step 4: Download output ────────────────────────────────────────
echo "── Step 4: Downloading trained model ──"

OUTPUT_DIR="${PROJECT_DIR}/certainty_workspace/model"
mkdir -p "$OUTPUT_DIR"

$KAGGLE kernels output "$KERNEL_SLUG" -p "$OUTPUT_DIR"

echo ""
echo "============================================"
echo "  Training complete!"
echo "============================================"
echo ""
echo "Output files:"
ls -la "$OUTPUT_DIR/"
echo ""
echo "Model:     ${OUTPUT_DIR}/ebm_certainty_model.pt"
echo "Tokenizer: ${OUTPUT_DIR}/ebm_certainty_tokenizer/"
echo "Metrics:   ${OUTPUT_DIR}/ebm_certainty_metrics.json"
echo ""
echo "To use the model:"
echo "  from certainty.inference.reranker import ConstraintReranker"
echo "  reranker = ConstraintReranker("
echo "      model_path='${OUTPUT_DIR}/ebm_certainty_model.pt',"
echo "      tokenizer_path='${OUTPUT_DIR}/ebm_certainty_tokenizer',"
echo "  )"
