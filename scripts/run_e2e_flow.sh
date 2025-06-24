#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------------------------------------
# Run the full real end-to-end workflow test and check logs for completion.
# ----------------------------------------------------------------------------
LOGFILE="e2e_test.log"

echo "🚀 Starting real end-to-end flow test..."
python3 backend/test_real_e2e_complete.py 2>&1 | tee "$LOGFILE"

# Look for the test summary indicating full pass
if grep -q "END-TO-END TEST PASSED" "$LOGFILE"; then
  echo "✅ End-to-end flow test PASSED"
  exit 0
else
  echo "❌ End-to-end flow test FAILED. Check $LOGFILE for details."
  exit 1
fi