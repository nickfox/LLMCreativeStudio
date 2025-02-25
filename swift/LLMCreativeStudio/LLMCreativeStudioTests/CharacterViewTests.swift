// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudioTests/CharacterViewTests.swift

import XCTest
import SwiftUI
@testable import LLMCreativeStudio

final class CharacterViewTests: XCTestCase {
    
    var networkManager: NetworkManager!
    
    override func setUp() {
        super.setUp()
        networkManager = NetworkManager()
    }
    
    override func tearDown() {
        networkManager = nil
        super.tearDown()
    }
    
    // Basic model tests that don't require ViewInspector
    
    func testCharacterModel() {
        // Create a test character
        let character = Character(
            id: "1",
            character_name: "John Lennon",
            llm_name: "claude",
            background: "Songwriter from Liverpool",
            created_at: "2023-01-01T00:00:00Z"
        )
        
        // Verify the character properties
        XCTAssertEqual(character.id, "1")
        XCTAssertEqual(character.character_name, "John Lennon")
        XCTAssertEqual(character.llm_name, "claude")
        XCTAssertEqual(character.background, "Songwriter from Liverpool")
        XCTAssertEqual(character.created_at, "2023-01-01T00:00:00Z")
    }
    
    func testNetworkManagerCharacterState() {
        // Set a current project
        let project = Project(
            id: "1",
            name: "Test Project",
            type: "creative",
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        networkManager.currentProject = project
        
        // Add some test characters
        let character1 = Character(
            id: "1",
            character_name: "John Lennon",
            llm_name: "claude",
            background: "Songwriter from Liverpool",
            created_at: "2023-01-01T00:00:00Z"
        )
        
        let character2 = Character(
            id: "2",
            character_name: "Paul McCartney",
            llm_name: "chatgpt",
            background: "Bassist from Liverpool",
            created_at: "2023-01-01T00:00:00Z"
        )
        
        networkManager.characters = [character1, character2]
        
        // Verify the characters were added correctly
        XCTAssertEqual(networkManager.characters.count, 2)
        XCTAssertEqual(networkManager.characters[0].character_name, "John Lennon")
        XCTAssertEqual(networkManager.characters[1].character_name, "Paul McCartney")
    }
    
    func testGetSenderName() {
        // Add a character to the NetworkManager
        let character = Character(
            id: "1",
            character_name: "John Lennon",
            llm_name: "claude",
            background: "Songwriter from Liverpool",
            created_at: "2023-01-01T00:00:00Z"
        )
        
        networkManager.characters = [character]
        
        // Test that getSenderName returns the character name for the LLM
        XCTAssertEqual(networkManager.getSenderName(for: "claude"), "John Lennon")
        
        // Test that getSenderName returns the default name for LLMs without characters
        XCTAssertEqual(networkManager.getSenderName(for: "chatgpt"), "ChatGPT")
        XCTAssertEqual(networkManager.getSenderName(for: "gemini"), "Gemini")
        XCTAssertEqual(networkManager.getSenderName(for: "user"), "nick")
    }
    
    func testParseMessageWithCharacter() {
        // Add a character to the NetworkManager
        let character = Character(
            id: "1",
            character_name: "John",
            llm_name: "claude",
            background: "Songwriter from Liverpool",
            created_at: "2023-01-01T00:00:00Z"
        )
        
        let project = Project(
            id: "1",
            name: "Test Project",
            type: "creative",
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        
        networkManager.currentProject = project
        networkManager.characters = [character]
        
        // Test parsing a message with a character mention
        let result = networkManager.parseMessage("@John what do you think?")
        XCTAssertEqual(result.llmName, "claude")
        XCTAssertEqual(result.parsedMessage, "what do you think?")
        
        // Test parsing a message with a character name at the beginning
        let result2 = networkManager.parseMessage("John, what do you think?")
        XCTAssertEqual(result2.llmName, "claude")
        XCTAssertEqual(result2.parsedMessage, "what do you think?")
    }

    // Note: The UI tests have been commented out as they require ViewInspector
    // To enable them, add ViewInspector to the project via Swift Package Manager
    
    /*
    func testCharacterViewWithNoCharacters() throws {
        // Create the view with empty characters list
        let view = CharacterView()
            .environmentObject(networkManager)
        
        // This requires ViewInspector to test the UI
    }
    
    func testCharacterViewWithNoProject() throws {
        // Create the view with no project selected
        let view = CharacterView()
            .environmentObject(networkManager)
        
        // This requires ViewInspector to test the UI
    }
    
    func testAddCharacterView() throws {
        // Set a current project
        let project = Project(
            id: "1",
            name: "Test Project",
            type: "creative",
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        networkManager.currentProject = project
        
        let view = AddCharacterView()
            .environmentObject(networkManager)
        
        // This requires ViewInspector to test the UI
    }
    */
}
