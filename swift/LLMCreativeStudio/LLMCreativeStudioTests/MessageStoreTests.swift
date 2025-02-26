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
        
        // Add a message
        messageStore.addMessage(
            text: "Test message",
            sender: "user",
            senderName: "Test User"
        )
        
        // Verify message was added
        XCTAssertEqual(messageStore.messages.count, 1)
        XCTAssertEqual(messageStore.messages[0].text, "Test message")
        XCTAssertEqual(messageStore.messages[0].sender, "user")
        XCTAssertEqual(messageStore.messages[0].senderName, "Test User")
    }
    
    func testClearMessages() {
        // Add some messages
        messageStore.addMessage(text: "Message 1", sender: "user", senderName: "User")
        messageStore.addMessage(text: "Message 2", sender: "claude", senderName: "Claude")
        
        // Verify messages were added
        XCTAssertEqual(messageStore.messages.count, 2)
        
        // Clear messages
        messageStore.clearMessages()
        
        // Verify messages were cleared
        XCTAssertEqual(messageStore.messages.count, 0)
    }
    
    // MARK: - Message Parsing Tests
    
    func testParseMessageWithMention() {
        // Create test characters
        let characters = [
            Character(
                id: "1",
                character_name: "John",
                llm_name: "claude",
                background: "",
                created_at: ""
            )
        ]
        
        // Test @mentions
        let (llm1, message1, dataQuery1) = messageStore.parseMessage("@claude Hello Claude", characters: characters)
        XCTAssertEqual(llm1, "claude")
        XCTAssertEqual(message1, "Hello Claude")
        XCTAssertEqual(dataQuery1, "")
        
        // Test @a shorthand
        let (llm2, message2, _) = messageStore.parseMessage("@a Hello again", characters: characters)
        XCTAssertEqual(llm2, "claude")
        XCTAssertEqual(message2, "Hello again")
        
        // Test @c shorthand
        let (llm3, message3, _) = messageStore.parseMessage("@c Hello ChatGPT", characters: characters)
        XCTAssertEqual(llm3, "chatgpt")
        XCTAssertEqual(message3, "Hello ChatGPT")
        
        // Test @g shorthand
        let (llm4, message4, _) = messageStore.parseMessage("@g Hello Gemini", characters: characters)
        XCTAssertEqual(llm4, "gemini")
        XCTAssertEqual(message4, "Hello Gemini")
        
        // Test @q shorthand (for data queries)
        let (llm5, message5, dataQuery5) = messageStore.parseMessage("@q What is the meaning of life?", characters: characters)
        XCTAssertEqual(llm5, "gemini")
        XCTAssertEqual(message5, "")
        XCTAssertEqual(dataQuery5, "What is the meaning of life?")
    }
    
    func testParseMessageWithCharacterAddressing() {
        // Create test characters
        let characters = [
            Character(
                id: "1",
                character_name: "John Lennon",
                llm_name: "claude",
                background: "",
                created_at: ""
            ),
            Character(
                id: "2",
                character_name: "Paul McCartney",
                llm_name: "chatgpt",
                background: "",
                created_at: ""
            )
        ]
        
        // Test character addressing with comma
        let (llm1, message1, _) = messageStore.parseMessage("John Lennon, how are you?", characters: characters)
        XCTAssertEqual(llm1, "claude")
        XCTAssertEqual(message1, "how are you?")
        
        // Test character addressing with space
        let (llm2, message2, _) = messageStore.parseMessage("Paul McCartney what's your favorite song?", characters: characters)
        XCTAssertEqual(llm2, "chatgpt")
        XCTAssertEqual(message2, "what's your favorite song?")
        
        // Test case insensitivity
        let (llm3, message3, _) = messageStore.parseMessage("john lennon, hello there", characters: characters)
        XCTAssertEqual(llm3, "claude")
        XCTAssertEqual(message3, "hello there")
        
        // Test message with no addressing
        let (llm4, message4, _) = messageStore.parseMessage("Hello everyone", characters: characters)
        XCTAssertEqual(llm4, "all")
        XCTAssertEqual(message4, "Hello everyone")
    }
    
    func testGetSenderName() {
        // Create test characters
        let characters = [
            Character(
                id: "1",
                character_name: "John Lennon",
                llm_name: "claude",
                background: "",
                created_at: ""
            ),
            Character(
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
        
        // Get recent context
        let context = messageStore.getRecentContext()
        
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
    }
}