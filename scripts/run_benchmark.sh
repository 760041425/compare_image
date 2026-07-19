#!/bin/bash
# Image Compare Benchmark — one-click launcher
# Usage: bash scripts/run_benchmark.sh

set -e

# Navigate to project root
cd "$(dirname "$0")/.."

PYTHON="/opt/miniconda3/bin/python3"

echo "============================================"
echo "  Image Compare — Algorithm Benchmark"
echo "============================================"
echo ""

# Check Python
if [ ! -x "$PYTHON" ]; then
    echo "❌ Python not found at $PYTHON"
    echo "   Please install miniconda or update the PYTHON path in this script."
    exit 1
fi

echo "Python: $($PYTHON --version)"
echo "Working directory: $(pwd)"
echo ""

# Check required files
if [ ! -f "data/242d929f1b68303b2f7edbff10c14427.mp4" ]; then
    echo "❌ Video file not found: data/242d929f1b68303b2f7edbff10c14427.mp4"
    exit 1
fi

if [ ! -f "query_image/f04eb4d677dfc38ac2304575aaf80dfa.jpg" ]; then
    echo "❌ Query image not found: query_image/f04eb4d677dfc38ac2304575aaf80dfa.jpg"
    exit 1
fi

# Create output directories
mkdir -p reports/visualizations

# Run benchmark
echo "Starting benchmark..."
echo ""
$PYTHON scripts/benchmark_algorithms.py

echo ""

# Open report
REPORT="reports/benchmark_report.html"
if [ -f "$REPORT" ]; then
    echo "📊 Opening report..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$REPORT"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        xdg-open "$REPORT" 2>/dev/null || echo "Report saved to: $REPORT"
    else
        echo "Report saved to: $REPORT"
    fi
else
    echo "❌ Report was not generated."
    exit 1
fi
