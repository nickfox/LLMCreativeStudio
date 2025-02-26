// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudioTests/MessageModelTests.swift

import XCTest
@testable import LLMCreativeStudio

class MessageModelTests: XCTestCase {
    
    func testMessageCreationWithDebateProperties() {
        // Create a message with all debate-specific properties
        let message = Message(
            text: "This is a test message",
            sender: "claude",
            senderName: "Claude",
            timestamp: Date(),
            referencedMessageId: nil,
            conversationMode: "debate",
            messageIntent: "response",
            debateRound: 2,
            debateState: "ROUND_2_QUESTIONING",
            waitingForUser: false,
            actionRequired: nil
        )
        
        // Test that all properties are set correctly
        XCTAssertEqual(message.text, "This is a test message")
        XCTAssertEqual(message.sender, "claude")
        XCTAssertEqual(message.senderName, "Claude")
        XCTAssertEqual(message.conversationMode, "debate")
        XCTAssertEqual(message.messageIntent, "response")
        XCTAssertEqual(message.debateRound, 2)
        XCTAssertEqual(message.debateState, "ROUND_2_QUESTIONING")
        XCTAssertEqual(message.waitingForUser, false)
        XCTAssertNil(message.actionRequired)
    }
    
    func testMessageWithUserInputPrompt() {
        // Create a message that indicates waiting for user input
        let message = Message(
            text: "Please provide your perspective on this topic",
            sender: "system",
            senderName: "System",
            debateRound: 1,
            debateState: "ROUND_1_USER_INPUT",
            waitingForUser: true,
            actionRequired: "debate_input"
        )
        
        // Test that all properties are set correctly
        XCTAssertEqual(message.text, "Please provide your perspective on this topic")
        XCTAssertEqual(message.sender, "system")
        XCTAssertEqual(message.senderName, "System")
        XCTAssertEqual(message.debateRound, 1)
        XCTAssertEqual(message.debateState, "ROUND_1_USER_INPUT")
        XCTAssertEqual(message.waitingForUser, true)
        XCTAssertEqual(message.actionRequired, "debate_input")
    }
    
    func testFormattedTimestamp() {
        // Create a message with a specific timestamp
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        let date = dateFormatter.date(from: "2023-01-01 14:30:00")!
        
        let message = Message(
            text: "Test message",
            sender: "user",
            senderName: "nick",
            timestamp: date
        )
        
        // Test the formatted timestamp
        XCTAssertTrue(message.formattedTimestamp.contains("2:30"))
        XCTAssertTrue(message.formattedTimestamp.contains("pm"))
        XCTAssertTrue(message.formattedTimestamp.contains("Jan 1, 2023"))
    }
    
    func testDefaultValues() {
        // Create a message with minimal parameters
        let message = Message(
            text: "Simple message",
            sender: "user",
            senderName: "nick"
        )
        
        // Test that default values are applied
        XCTAssertNil(message.referencedMessageId)
        XCTAssertNil(message.conversationMode)
        XCTAssertNil(message.messageIntent)
        XCTAssertNil(message.debateRound)
        XCTAssertNil(message.debateState)
        XCTAssertNil(message.waitingForUser)
        XCTAssertNil(message.actionRequired)
    }
}
