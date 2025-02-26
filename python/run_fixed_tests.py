#!/usr/bin/env python3
"""
Script to run specific fixed tests to verify our fixes.
"""

import sys
import subprocess
import os
import time

def main():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # The specific tests to run
    test_files = [
        "test_conversation.py",
        "tests/test_debate_user_participation.py::test_debate_user_participation_flow",
        "tests/test_llms.py::test_claude_autogen_response",
        "tests/test_llms.py::test_chatgpt_autogen_response",
        "tests/test_llms.py::test_gemini_autogen_response"
    ]
    
    # Run with -v for verbose output
    cmd = ["python", "-m", "pytest"] + test_files + ["-v"]
    
    # Create timestamp for log file
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = f"logs/fixed-tests-{timestamp}.log"
    
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
        
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
