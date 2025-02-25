// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudioTests/MessageTests.swift

import XCTest
@testable import LLMCreativeStudio

final class MessageTests: XCTestCase {
    
    func testMessageCreation() {
        // Create a message
        let text = "Hello, world!"
        let sender = "user"
        let senderName = "nick"
        let timestamp = Date()
        let referencedMessageId = UUID()
        let conversationMode = "open"
        let messageIntent = "question"
        
        let message = Message(
            text: text,
            sender: sender,
            senderName: senderName,
            timestamp: timestamp,
            referencedMessageId: referencedMessageId,
            conversationMode: conversationMode,
            messageIntent: messageIntent
        )
        
        // Check that the properties were set correctly
        XCTAssertEqual(message.text, text)
        XCTAssertEqual(message.sender, sender)
        XCTAssertEqual(message.senderName, senderName)
        XCTAssertEqual(message.timestamp, timestamp)
        XCTAssertEqual(message.referencedMessageId, referencedMessageId)
        XCTAssertEqual(message.conversationMode, conversationMode)
        XCTAssertEqual(message.messageIntent, messageIntent)
    }
    
    func testFormattedTimestamp() {
        // Create a message with a specific timestamp
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        
        guard let timestamp = dateFormatter.date(from: "2023-06-15 14:30:00") else {
            XCTFail("Failed to create test date")
            return
        }
        
        let message = Message(
            text: "Test message",
            sender: "user",
            senderName: "nick",
            timestamp: timestamp
        )
        
        // Get the formatted timestamp
        let formattedTimestamp = message.formattedTimestamp
        
        // Check that the timestamp is formatted correctly
        // Note: The exact format may depend on the locale and timezone
        // So we're just checking that it contains the essential parts
        XCTAssertTrue(formattedTimestamp.contains("2:30"))
        XCTAssertTrue(formattedTimestamp.contains("pm") || formattedTimestamp.contains("PM"))
        XCTAssertTrue(formattedTimestamp.contains("Jun"))
        XCTAssertTrue(formattedTimestamp.contains("15"))
        XCTAssertTrue(formattedTimestamp.contains("2023"))
    }
    
    func testMessageEquality() {
        // Create two messages with different content
        let message1 = Message(
            text: "Message 1",
            sender: "user",
            senderName: "nick"
        )
        
        let message2 = Message(
            text: "Message 2",
            sender: "claude",
            senderName: "Claude"
        )
        
        // Check that they have different IDs (since UUID is random)
        XCTAssertNotEqual(message1.id, message2.id)
    }
    
    func testOptionalProperties() {
        // Create a message with minimal properties
        let message = Message(
            text: "Simple message",
            sender: "user",
            senderName: "nick"
        )
        
        // Check that the optional properties are nil
        XCTAssertNil(message.referencedMessageId)
        XCTAssertNil(message.conversationMode)
        XCTAssertNil(message.messageIntent)
    }
}
