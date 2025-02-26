#!/usr/bin/env python3
"""
Script to run all tests with verbose output and a focus on a specific test file.
"""

import sys
import subprocess
import os
import time

def main():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # The specific test file to focus on
    focus_test = "tests/run_debate_test.py"
    
    # Run with -v for verbose output
    cmd = ["python", "-m", "pytest", focus_test, "-v"]
    
    # Create timestamp for log file
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = f"logs/pytest-{timestamp}.log"
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Logging to: {log_file}")
    
    try:
        # Run pytest with the specified arguments
        with open(log_file, 'w') as f:
            f.write(f"Running: {' '.join(cmd)}\n\n")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            # Write output to log file
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)
            
        # Print output to console
        print("\n=== TEST OUTPUT ===")
        print(result.stdout)
        
        if result.stderr:
            print("\n=== ERROR OUTPUT ===")
            print(result.stderr)
        
        # Return appropriate exit code
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
