// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudioTests/MessageBubbleTests.swift

import XCTest
import SwiftUI
@testable import LLMCreativeStudio

final class MessageBubbleTests: XCTestCase {
    
    func testExtractSources() {
        // Create a message with RAG sources in JSON format
        let messageText = """
        Here's the answer to your question about Swift.

        Sources:
        [
            {
                "document_id": "doc123",
                "chunk_id": 5,
                "similarity": 0.92,
                "text_preview": "Swift is a powerful programming language developed by Apple."
            },
            {
                "document_id": "doc456",
                "chunk_id": 2,
                "similarity": 0.85,
                "text_preview": "Swift combines modern language features with performance and safety."
            }
        ]
        """
        
        let message = Message(
            text: messageText,
            sender: "research_assistant",
            senderName: "Research Assistant"
        )
        
        // Create a MessageBubble with the message
        let bubble = MessageBubble(message: message)
        
        // Call the extractSources method directly now that it's internal
        let sources = bubble.extractSources(from: messageText)
        
        // Verify that the sources were extracted correctly
        XCTAssertNotNil(sources, "Sources should be extracted")
        XCTAssertEqual(sources?.count, 2, "Should extract 2 sources")
        
        // Verify the first source
        XCTAssertEqual(sources?[0].document_id, "doc123")
        XCTAssertEqual(sources?[0].chunk_id, 5)
        XCTAssertEqual(sources?[0].similarity, 0.92)
        XCTAssertEqual(sources?[0].text_preview, "Swift is a powerful programming language developed by Apple.")
        
        // Verify the second source
        XCTAssertEqual(sources?[1].document_id, "doc456")
        XCTAssertEqual(sources?[1].chunk_id, 2)
        XCTAssertEqual(sources?[1].similarity, 0.85)
        XCTAssertEqual(sources?[1].text_preview, "Swift combines modern language features with performance and safety.")
    }
    
    func testExtractSourcesWithInvalidFormat() {
        // Create a message with invalid JSON format
        let messageText = """
        Here's the answer to your question about Swift.

        Sources:
        This is not valid JSON
        """
        
        let message = Message(
            text: messageText,
            sender: "research_assistant",
            senderName: "Research Assistant"
        )
        
        // Create a MessageBubble with the message
        let bubble = MessageBubble(message: message)
        
        // Call the extractSources method directly
        let sources = bubble.extractSources(from: messageText)
        
        // Verify that no sources were extracted due to invalid format
        XCTAssertNil(sources, "No sources should be extracted from invalid JSON")
    }
    
    func testExtractSourcesWithNoSourcesSection() {
        // Create a message with no Sources section
        let messageText = "Here's the answer to your question about Swift."
        
        let message = Message(
            text: messageText,
            sender: "research_assistant",
            senderName: "Research Assistant"
        )
        
        // Create a MessageBubble with the message
        let bubble = MessageBubble(message: message)
        
        // Call the extractSources method directly
        let sources = bubble.extractSources(from: messageText)
        
        // Verify that no sources were extracted
        XCTAssertNil(sources, "No sources should be extracted when there's no Sources section")
    }
}