#!/usr/bin/env python3
# /Users/nickfox137/Documents/llm-creative-studio/python/run_tests.py

"""
Test runner for LLMCreativeStudio
This script runs all tests and captures errors to a log file

Usage:
    python run_tests.py                 # Run all tests
    python run_tests.py --verbose       # Run with detailed output
    python run_tests.py --test-file X   # Run specific test file
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Run tests for LLMCreativeStudio')
    parser.add_argument('--test-file', '-f', help='Specific test file to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')
    
    args = parser.parse_args()
    
    # Ensure the logs directory exists
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Determine the test path
    if args.test_file:
        test_path = os.path.join('tests', args.test_file)
    else:
        test_path = 'tests/'
    
    # Add pytest-asyncio to required plugins
    pytest_cmd = [sys.executable, '-m', 'pytest', test_path, '--no-header', '-xvs']
    
    if args.verbose:
        pytest_cmd.append('-v')
    
    print(f"Running tests with command: {' '.join(pytest_cmd)}")
    print(f"Logs will be saved to {log_dir}")
    
    try:
        # Run the tests and capture output
        subprocess.run(pytest_cmd, check=True)
        print(f"\nTests completed. Check the logs directory for details: {log_dir}")
    except subprocess.CalledProcessError as e:
        print(f"\nSome tests failed with exit code {e.returncode}. Check the logs directory for details: {log_dir}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
