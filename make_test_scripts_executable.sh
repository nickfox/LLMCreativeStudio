#!/bin/bash
# Script to make test runners executable
# To use: chmod +x make_test_scripts_executable.sh && ./make_test_scripts_executable.sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "Making test scripts executable..."

# Make Python test runner executable
chmod +x /Users/nickfox137/Documents/llm-creative-studio/python/run_tests.py
echo "✅ Made Python test runner executable"

# Make Swift test runner executable
chmod +x /Users/nickfox137/Documents/llm-creative-studio/swift/run_tests.sh
echo "✅ Made Swift test runner executable"

# Make the manual debate test executable
chmod +x /Users/nickfox137/Documents/llm-creative-studio/python/tests/run_debate_test.py
echo "✅ Made manual debate test executable"

echo "All test scripts now have execute permissions!"
echo "You can run them with:"
echo "  cd python && ./run_tests.py"
echo "  cd swift && ./run_tests.sh"
echo "  cd python && ./tests/run_debate_test.py"
