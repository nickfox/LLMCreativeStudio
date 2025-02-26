#!/bin/bash
# Make this script executable: chmod +x run_tests.sh
# Script to run SwiftUI tests for LLMCreativeStudio

set -e  # Exit immediately if a command exits with a non-zero status

echo "Running LLMCreativeStudio UI Tests..."

# Navigate to the Swift project directory
cd "$(dirname "$0")/LLMCreativeStudio"

# Check that xcodebuild is available
if ! command -v xcodebuild &> /dev/null; then
    echo "Error: xcodebuild is not available. Make sure Xcode is installed and the command line tools are set up."
    exit 1
fi

# Check that xcpretty is available, install if not
if ! command -v xcpretty &> /dev/null; then
    echo "xcpretty not found, installing..."
    gem install xcpretty
fi

# Check if ViewInspector is in the package dependencies, add it if not
if ! grep -q "ViewInspector" "LLMCreativeStudio.xcodeproj/project.pbxproj"; then
    echo "Adding ViewInspector package dependency..."
    # This would normally be done through Xcode interface
    # For a script, we would need to modify the project file directly which is complex
    echo "Please add ViewInspector package in Xcode: File > Swift Packages > Add Package Dependency"
    echo "URL: https://github.com/nalexn/ViewInspector"
    exit 1
fi

# Use xcodebuild to run the tests
echo "Running tests with xcodebuild..."
xcodebuild test \
  -project LLMCreativeStudio.xcodeproj \
  -scheme LLMCreativeStudio \
  -destination 'platform=macOS' \
  | xcpretty --color

# Check the exit code
if [ $? -eq 0 ]; then
  echo "✅ All tests passed!"
else
  echo "❌ Tests failed!"
  exit 1
fi
