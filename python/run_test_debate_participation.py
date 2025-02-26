#!/usr/bin/env python3
"""
Script to specifically run the debate participation test that was failing.
"""

import sys
import subprocess
import os

def main():
    # The specific test to run
    test_path = "tests/test_debate_user_participation.py::test_debate_user_participation_flow"
    
    # Run with -v for verbose output
    cmd = ["python", "-m", "pytest", test_path, "-v"]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        # Run pytest with the specified arguments
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Print output to console
        print("\n=== TEST OUTPUT ===")
        print(result.stdout)
        
        if result.stderr:
            print("\n=== ERROR OUTPUT ===")
            print(result.stderr)
        
        return result.returncode
    except Exception as e:
        print(f"Error running test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
