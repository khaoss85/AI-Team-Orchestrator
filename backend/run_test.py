import subprocess
import sys
import os

# Change to correct directory
os.chdir('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Run test
result = subprocess.run([sys.executable, 'auto_execution_test.py'], 
                       capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")