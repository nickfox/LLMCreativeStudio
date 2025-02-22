// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudioTests/NetworkManagerTests.swift

import XCTest
@testable import LLMCreativeStudio

final class NetworkManagerTests: XCTestCase {
    var networkManager: NetworkManager!
    
    override func setUp() {
        super.setUp()
        networkManager = NetworkManager()
    }
    
    override func tearDown() {
        networkManager = nil
        super.tearDown()
    }
    
    func testMessageParsing() {
        // Test @mentions parsing
        let test1 = networkManager.parseMessage("@c help me with this")
        XCTAssertEqual(test1.llmName, "chatgpt")
        XCTAssertEqual(test1.parsedMessage, "help me with this")
        XCTAssertEqual(test1.dataQuery, "")
        
        let test2 = networkManager.parseMessage("@a what do you think?")
        XCTAssertEqual(test2.llmName, "claude")
        XCTAssertEqual(test2.parsedMessage, "what do you think?")
        
        let test3 = networkManager.parseMessage("hello everyone")
        XCTAssertEqual(test3.llmName, "all")
        XCTAssertEqual(test3.parsedMessage, "hello everyone")
    }
    
    func testContextGeneration() {
        let expectation = XCTestExpectation(description: "Messages added")
        
        // Add test messages
        networkManager.addMessage(text: "First message", sender: "user", senderName: "nick")
        networkManager.addMessage(text: "Response one", sender: "claude", senderName: "Claude")
        networkManager.addMessage(text: "Follow up", sender: "user", senderName: "nick")
        
        // Give time for the async operations to complete
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let context = self.networkManager.getRecentContext()
            
            XCTAssertEqual(context.count, 3)
            XCTAssertEqual(context[0]["text"] as? String, "First message")
            XCTAssertEqual(context[0]["sender"] as? String, "user")
            
            // Test message references
            let referenceId = UUID()
            self.networkManager.addMessage(
                text: "Reference test",
                sender: "user",
                senderName: "nick",
                referencedMessageId: referenceId,
                messageIntent: "response"
            )
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                let updatedContext = self.networkManager.getRecentContext()
                let lastMessage = updatedContext.last!
                
                XCTAssertEqual(lastMessage["referencedMessageId"] as? String, referenceId.uuidString)
                XCTAssertEqual(lastMessage["messageIntent"] as? String, "response")
                
                expectation.fulfill()
            }
        }
        
        wait(for: [expectation], timeout: 2.0)
    }
}
