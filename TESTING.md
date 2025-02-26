# LLMCreativeStudio Testing Guide

This document explains how to run tests for both the Python backend and Swift frontend of LLMCreativeStudio, focusing on the enhanced debate system with user participation.

## Python Backend Tests

The Python tests verify the functionality of the debate system, including user participation, message routing, and state management.

### Setting Up Python Test Environment

Before running the tests, make sure you have installed the test dependencies:

```bash
cd /Users/nickfox137/Documents/llm-creative-studio/python
pip install -r pytest-requirements.txt
```

### Running All Python Tests

```bash
cd /Users/nickfox137/Documents/llm-creative-studio/python
python run_tests.py
```

For more detailed output:

```bash
python run_tests.py --verbose
```

### Running Specific Python Tests

To run just the debate user participation tests:

```bash
python run_tests.py --test-file test_debate_user_participation.py
```

### Running Manual Debate Test

We've also created a manual test script to simulate a debate with user participation:

```bash
python tests/run_debate_test.py
```

### Python Test Logs

Test logs are saved in the `logs` directory with timestamps for easy debugging.

## Swift Frontend Tests

The Swift tests verify the UI components for the debate system, including message styling, debate indicators, and user input prompts.

### Adding ViewInspector

Before running the tests, you need to add the ViewInspector package to your Xcode project:

1. Open the project in Xcode
2. Go to File > Swift Packages > Add Package Dependency
3. Enter the URL: `https://github.com/nalexn/ViewInspector`
4. Click Next, select the latest version, and click Finish

### Running Swift Tests

Use the provided script:

```bash
cd /Users/nickfox137/Documents/llm-creative-studio/swift
chmod +x run_tests.sh  # Make executable if needed
./run_tests.sh
```

Alternatively, you can run tests directly in Xcode:

1. Open the project in Xcode
2. Select the test navigator (⌘6)
3. Click the play button next to the tests you want to run

## Test Descriptions

### Python Tests
- `test_debate_user_participation.py`: Tests the full debate flow with user participation
- `test_conversation_manager.py`: Tests message routing and command handling
- `run_debate_test.py`: Manual test script for simulating a debate

### Swift Tests
- `DebateUITests.swift`: Tests for UI components including MessageBubble, DebateStatusView, and DebateInputPromptView
- `NetworkManagerDebateTests.swift`: Tests for processing debate messages and user input
- `MessageModelTests.swift`: Tests for the Message model with debate properties

## Continuous Integration

For CI/CD purposes, all tests are designed to run without requiring manual intervention. The testing logs provide detailed output for debugging purposes.

## Troubleshooting

If you encounter issues with the tests:

1. Make sure you've installed all dependencies
2. Check the test logs for detailed error messages
3. Verify that ViewInspector is properly installed for Swift tests
4. Ensure the Python environment is set up correctly
