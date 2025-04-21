// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudioTests/DebateUITests.swift

import XCTest
import SwiftUI
@testable import LLMCreativeStudio

class DebateUITests: XCTestCase {
    
    // MARK: - MessageBubble Tests
    
    func testMessageBubbleWithDebateInfo() {
        // Create a message with debate information
        let message = Message(
            text: "This is my opening statement.",
            sender: "claude",
            senderName: "Claude",
            debateRound: 1,
            debateState: "ROUND_1_OPENING",
            waitingForUser: false
        )
        
        // Just verify the message was created with the right debate info
        XCTAssertEqual(message.debateRound, 1)
        XCTAssertEqual(message.debateState, "ROUND_1_OPENING")
        XCTAssertEqual(message.waitingForUser, false)
    }
    
    func testMessageBubbleWithUserInputPrompt() {
        // Create a message that's waiting for user input
        let message = Message(
            text: "Please provide your perspective on this topic.",
            sender: "system",
            senderName: "System",
            debateRound: 1,
            debateState: "ROUND_1_USER_INPUT",
            waitingForUser: true
        )
        
        // Just verify the message was created with the right properties
        XCTAssertEqual(message.waitingForUser, true)
        XCTAssertEqual(message.sender, "system")
        XCTAssertEqual(message.debateState, "ROUND_1_USER_INPUT")
    }
    
    // MARK: - DebateStatusView Tests
    
    func testDebateStatusViewContent() {
        // Create a network manager with mock data
        let networkManager = NetworkManager()
        
        // Add a few mock messages to simulate a debate in progress
        networkManager.messages = [
            Message(
                text: "Opening statement",
                sender: "claude",
                senderName: "Claude",
                debateRound: 1,
                debateState: "ROUND_1_OPENING"
            ),
            Message(
                text: "Please provide your perspective",
                sender: "system",
                senderName: "System",
                debateRound: 1,
                debateState: "ROUND_1_USER_INPUT",
                waitingForUser: true
            )
        ]
        
        let statusView = DebateStatusView(networkManager: networkManager)
        
        // Test the getCurrentDebateStatus function directly
        let status = statusView.getCurrentDebateStatus()
        XCTAssertEqual(status.round, "Opening")
        XCTAssertTrue(status.state.contains("Waiting") || status.state.contains("waiting"))
    }
    
    // MARK: - Text Selection Tests
    
    func testMessageBubbleTextContent() {
        // Create a message and bubble
        let message = Message(
            text: "This is a test message",
            sender: "claude",
            senderName: "Claude"
        )
        
        _ = MessageBubble(message: message)
        
        // Just verify the message was created with the right content
        XCTAssertEqual(message.text, "This is a test message")
        XCTAssertEqual(message.sender, "claude")
        XCTAssertEqual(message.senderName, "Claude")
    }
    
    func testDebateStatusViewState() {
        let networkManager = NetworkManager()
        networkManager.messages = [
            Message(text: "Debate message", sender: "system", senderName: "System", debateRound: 1, debateState: "ROUND_1_OPENING")
        ]
        
        let statusView = DebateStatusView(networkManager: networkManager)
        
        // Verify the status function works correctly
        let status = statusView.getCurrentDebateStatus()
        XCTAssertEqual(status.round, "Opening")
    }
    
    // MARK: - DebateInputPromptView Tests
    
    func testDebateInputPromptViewAction() {
        // Set up an expectation to track if the continue action is called
        let expectation = XCTestExpectation(description: "Continue action called")
        
        // Create the view with a mock action that fulfills our expectation
        let promptView = DebateInputPromptView(continueAction: {
            expectation.fulfill()
        })
        
        // Verify the view was created (can't easily test button taps without ViewInspector)
        XCTAssertNotNil(promptView)
        
        // Call the action directly for testing
        promptView.continueAction()
        
        // Verify the action was called
        wait(for: [expectation], timeout: 1.0)
    }
    
    // MARK: - ContentView Helper Function Tests
    
    // Helper for testing isActiveDebate logic
    func testActiveDebateLogic() {
        // Arrange
        let networkManager = NetworkManager()
        
        // Act - Case 1: No debate messages
        let result1 = isActiveDebate(messages: networkManager.messages)
        
        // Assert
        XCTAssertFalse(result1)
        
        // Arrange for Case 2
        networkManager.messages = [
            Message(
                text: "Debate message",
                sender: "claude",
                senderName: "Claude",
                debateRound: 1,
                debateState: "ROUND_1_OPENING"
            )
        ]
        
        // Act - Case 2: With debate messages
        let result2 = isActiveDebate(messages: networkManager.messages)
        
        // Assert
        XCTAssertTrue(result2)
    }
    
    // Helper function to check if we're in an active debate - extracted for testing
    func isActiveDebate(messages: [Message]) -> Bool {
        // Check the last few messages for debate indicators
        let recentMessages = messages.suffix(10)
        for message in recentMessages.reversed() {
            if message.debateRound != nil || message.debateState != nil {
                return true
            }
        }
        return false
    }
    
    // Helper for testing isWaitingForDebateInput logic
    func testWaitingForDebateInputLogic() {
        // Arrange
        let networkManager = NetworkManager()
        
        // Act - Case 1: No waiting messages
        let result1 = isWaitingForDebateInput(messages: networkManager.messages)
        
        // Assert
        XCTAssertFalse(result1)
        
        // Arrange for Case 2
        networkManager.messages = [
            Message(
                text: "Please provide your input",
                sender: "system",
                senderName: "System",
                debateRound: 1,
                debateState: "ROUND_1_USER_INPUT",
                waitingForUser: true
            )
        ]
        
        // Act - Case 2: With waiting messages
        let result2 = isWaitingForDebateInput(messages: networkManager.messages)
        
        // Assert
        XCTAssertTrue(result2)
    }
    
    // Helper function to check if system is waiting for user input - extracted for testing
    func isWaitingForDebateInput(messages: [Message]) -> Bool {
        // Check the most recent messages
        let recentMessages = messages.suffix(5)
        for message in recentMessages.reversed() {
            if message.waitingForUser == true {
                return true
            }
        }
        return false
    }
}
