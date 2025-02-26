#!/usr/bin/env python3
"""
Debug script for running a specific test file with detailed output.
"""

import sys
import subprocess
import os

def main():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Run the specific test with verbose output
    test_file = "tests/run_debate_test.py"
    print(f"Running test: {test_file}")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_file, "-v"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Output results
        print("\n--- STDOUT ---")
        print(result.stdout)
        
        print("\n--- STDERR ---")
        print(result.stderr)
        
        # Write to log file
        log_path = os.path.join('logs', 'test_debug.log')
        with open(log_path, 'w') as f:
            f.write("--- STDOUT ---\n")
            f.write(result.stdout)
            f.write("\n\n--- STDERR ---\n")
            f.write(result.stderr)
        
        print(f"\nLog written to: {log_path}")
        
        # Return appropriate exit code
        return result.returncode
    except Exception as e:
        print(f"Error running test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
