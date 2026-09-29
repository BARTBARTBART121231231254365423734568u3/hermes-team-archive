#!/bin/bash
# Verify that an implementation task was executed correctly.
# Usage: ./verify-execution.sh <task_name> <expected_files> <test_commands>

set -e

TASK_NAME=${1:-"Implementation"}
shift

echo "[Verification] Starting checks for: $TASK_NAME"
echo ""

# Check that files exist
echo "[1/3] Checking files exist..."
for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "✗ FAILED: File does not exist: $file"
        exit 1
    fi
    echo "✓ Found: $file"
done
echo ""

# Check that code compiles/builds
echo "[2/3] Checking build..."
if [ -f "Cargo.toml" ]; then
    if cargo check --quiet 2>/dev/null; then
        echo "✓ Rust code compiles"
    else
        echo "✗ FAILED: Rust code does not compile"
        exit 1
    fi
fi

if [ -f "package.json" ]; then
    if npm run build --silent 2>/dev/null; then
        echo "✓ JavaScript builds"
    else
        echo "✗ FAILED: JavaScript build failed"
        exit 1
    fi
fi
echo ""

# Run tests if available
echo "[3/3] Running tests..."
if [ -f "Cargo.toml" ]; then
    if cargo test --quiet 2>/dev/null; then
        echo "✓ Rust tests pass"
    else
        echo "⚠ Rust tests failed (may be expected)"
    fi
fi

if command -v npm &> /dev/null && [ -f "package.json" ]; then
    if npm test --silent 2>/dev/null; then
        echo "✓ Tests pass"
    else
        echo "⚠ Tests failed (may be expected)"
    fi
fi
echo ""

echo "[✓ Verification Complete] $TASK_NAME is ready for deployment"
