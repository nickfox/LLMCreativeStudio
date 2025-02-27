import XCTest
@testable import LLMCreativeStudio

class MessageStoreTests: XCTestCase {
    var messageStore: MessageStore!
    
    override func setUp() {
        super.setUp()
        messageStore = MessageStore()
    }
    
    override func tearDown() {
        messageStore = nil
        super.tearDown()
    }
    
    // MARK: - Basic Functionality Tests
    
    func testAddMessage() {
        // Initial state
        XCTAssertEqual(messageStore.messages.count, 0)
        
        // When adding message to MessageStore, need to account for DispatchQueue.main.async
        let expectation = XCTestExpectation(description: "Message added")
        
        // Add a message
        messageStore.addMessage(
            text: "Test message",
            sender: "user",
            senderName: "Test User"
        )
        
        // Wait for async operation to complete
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            // Verify message was added
            XCTAssertEqual(self.messageStore.messages.count, 1)
            if self.messageStore.messages.count > 0 {
                XCTAssertEqual(self.messageStore.messages[0].text, "Test message")
                XCTAssertEqual(self.messageStore.messages[0].sender, "user")
                XCTAssertEqual(self.messageStore.messages[0].senderName, "Test User")
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 1.0)
    }
    
    func testClearMessages() {
        // Add some messages and wait for them to be processed
        let expectation = XCTestExpectation(description: "Messages cleared")
        
        messageStore.addMessage(text: "Message 1", sender: "user", senderName: "User")
        messageStore.addMessage(text: "Message 2", sender: "claude", senderName: "Claude")
        
        // Wait for async operations to complete
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            // Verify messages were added
            XCTAssertGreaterThanOrEqual(self.messageStore.messages.count, 1)
            
            // Clear messages
            self.messageStore.clearMessages()
            
            // Wait for clear operation to complete
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                // Verify messages were cleared
                XCTAssertEqual(self.messageStore.messages.count, 0)
                expectation.fulfill()
            }
        }
        
        wait(for: [expectation], timeout: 1.0)
    }
    
    // MARK: - Message Parsing Tests
    
    func testParseMessageWithMention() {
        // Create test characters
        let characters = [
            CharacterModel(
                id: "1",
                character_name: "John",
                llm_name: "claude",
                background: "",
                created_at: ""
            )
        ]
        
        // Test @mentions
        let result1 = messageStore.parseMessage("@claude Hello Claude", characters: characters)
        XCTAssertEqual(result1.llmName, "claude")
        XCTAssertEqual(result1.parsedMessage, "Hello Claude")
        XCTAssertEqual(result1.dataQuery, "")
        
        // Test @a shorthand
        let result2 = messageStore.parseMessage("@a Hello again", characters: characters)
        XCTAssertEqual(result2.llmName, "claude")
        XCTAssertEqual(result2.parsedMessage, "Hello again")
        
        // Test @c shorthand
        let result3 = messageStore.parseMessage("@c Hello ChatGPT", characters: characters)
        XCTAssertEqual(result3.llmName, "chatgpt")
        XCTAssertEqual(result3.parsedMessage, "Hello ChatGPT")
        
        // Test @g shorthand
        let result4 = messageStore.parseMessage("@g Hello Gemini", characters: characters)
        XCTAssertEqual(result4.llmName, "gemini")
        XCTAssertEqual(result4.parsedMessage, "Hello Gemini")
        
        // Test @q shorthand (for data queries)
        let result5 = messageStore.parseMessage("@q What is the meaning of life?", characters: characters)
        XCTAssertEqual(result5.llmName, "gemini")
        XCTAssertEqual(result5.parsedMessage, "")
        XCTAssertEqual(result5.dataQuery, "What is the meaning of life?")
    }
    
    func testParseMessageWithCharacterAddressing() {
        // Create test characters
        let characters = [
            CharacterModel(
                id: "1",
                character_name: "John Lennon",
                llm_name: "claude",
                background: "",
                created_at: ""
            ),
            CharacterModel(
                id: "2",
                character_name: "Paul McCartney",
                llm_name: "chatgpt",
                background: "",
                created_at: ""
            )
        ]
        
        // Test character addressing with comma
        let result1 = messageStore.parseMessage("John Lennon, how are you?", characters: characters)
        XCTAssertEqual(result1.llmName, "claude")
        XCTAssertEqual(result1.parsedMessage, "how are you?")
        
        // Test character addressing with space
        let result2 = messageStore.parseMessage("Paul McCartney what's your favorite song?", characters: characters)
        XCTAssertEqual(result2.llmName, "chatgpt")
        XCTAssertEqual(result2.parsedMessage, "what's your favorite song?")
        
        // Test case insensitivity
        let result3 = messageStore.parseMessage("john lennon, hello there", characters: characters)
        XCTAssertEqual(result3.llmName, "claude")
        XCTAssertEqual(result3.parsedMessage, "hello there")
        
        // Test message with no addressing
        let result4 = messageStore.parseMessage("Hello everyone", characters: characters)
        XCTAssertEqual(result4.llmName, "all")
        XCTAssertEqual(result4.parsedMessage, "Hello everyone")
    }
    
    func testGetSenderName() {
        // Create test characters
        let characters = [
            CharacterModel(
                id: "1",
                character_name: "John Lennon",
                llm_name: "claude",
                background: "",
                created_at: ""
            ),
            CharacterModel(
                id: "2",
                character_name: "Paul McCartney",
                llm_name: "chatgpt",
                background: "",
                created_at: ""
            )
        ]
        
        // Test with character assigned
        let name1 = messageStore.getSenderName(for: "claude", characters: characters)
        XCTAssertEqual(name1, "John Lennon")
        
        let name2 = messageStore.getSenderName(for: "chatgpt", characters: characters)
        XCTAssertEqual(name2, "Paul McCartney")
        
        // Test without character assigned
        let name3 = messageStore.getSenderName(for: "gemini", characters: characters)
        XCTAssertEqual(name3, "Gemini")
        
        // Test system sender
        let name4 = messageStore.getSenderName(for: "system", characters: characters)
        XCTAssertEqual(name4, "System")
        
        // Test user sender
        let name5 = messageStore.getSenderName(for: "user", characters: characters)
        XCTAssertEqual(name5, "You")
        
        // Test unknown sender
        let name6 = messageStore.getSenderName(for: "unknown", characters: characters)
        XCTAssertEqual(name6, "Unknown")
    }
    
    func testGetRecentContext() {
        let expectation = XCTestExpectation(description: "Messages added and context fetched")
        
        // Add some test messages with various properties
        for i in 1...10 {
            messageStore.addMessage(
                text: "Message \(i)",
                sender: i % 2 == 0 ? "user" : "claude",
                senderName: i % 2 == 0 ? "User" : "Claude",
                referencedMessageId: i % 3 == 0 ? UUID() : nil,
                messageIntent: i % 4 == 0 ? "question" : nil
            )
        }
        
        // Wait for async operations to complete
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            // Get recent context
            let context = self.messageStore.getRecentContext()
            
            // Since we added 10 messages, we should get the 5 most recent ones
            XCTAssertEqual(context.count, 5)
            
            // Check the format of the context
            for (index, item) in context.enumerated() {
                let messageIndex = 10 - 4 + index  // 6, 7, 8, 9, 10
                
                XCTAssertNotNil(item["id"])
                XCTAssertEqual(item["text"] as? String, "Message \(messageIndex)")
                XCTAssertEqual(item["sender"] as? String, messageIndex % 2 == 0 ? "user" : "claude")
                XCTAssertEqual(item["senderName"] as? String, messageIndex % 2 == 0 ? "User" : "Claude")
                
                // Check optional fields
                if messageIndex % 3 == 0 {
                    XCTAssertNotNil(item["referencedMessageId"])
                }
                
                if messageIndex % 4 == 0 {
                    XCTAssertEqual(item["messageIntent"] as? String, "question")
                }
            }
            
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 1.0)
    }
}