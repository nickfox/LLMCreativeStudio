import Foundation
import Combine

// Protocol for the message store, enabling easier testing
protocol MessageStoreProtocol {
    var messages: [Message] { get }
    var messagesPublisher: Published<[Message]>.Publisher { get }
    
    func addMessage(text: String, sender: String, senderName: String, referencedMessageId: UUID?, messageIntent: String?)
    func clearMessages()
    func parseMessage(_ message: String, characters: [CharacterModel]) -> (llmName: String, parsedMessage: String, dataQuery: String)
    func getSenderName(for llmName: String, characters: [CharacterModel]) -> String
    func getRecentContext() -> [[String: Any]]
}

// Main implementation of the message store
class MessageStore: MessageStoreProtocol, ObservableObject {
    @Published var messages: [Message] = []
    
    var messagesPublisher: Published<[Message]>.Publisher { $messages }
    
    func addMessage(text: String, sender: String, senderName: String, referencedMessageId: UUID? = nil, messageIntent: String? = nil) {
        let newMessage = Message(
            text: text,
            sender: sender,
            senderName: senderName,
            referencedMessageId: referencedMessageId,
            messageIntent: messageIntent
        )
        
        DispatchQueue.main.async {
            self.messages.append(newMessage)
        }
    }
    
    func clearMessages() {
        DispatchQueue.main.async {
            self.messages = []
        }
    }
    
    func parseMessage(_ message: String, characters: [CharacterModel]) -> (llmName: String, parsedMessage: String, dataQuery: String) {
        // Regular expression for @mentions
        let mentionRegex = try! NSRegularExpression(pattern: "@([a-zA-Z]+)", options: [])
        let matches = mentionRegex.matches(in: message, options: [], range: NSRange(location: 0, length: message.utf16.count))
        
        var llmName = "all"
        var dataQuery = ""
        var parsedMessage = message
        
        // Check for @mentions
        if let match = matches.first {
            let mentionRange = Range(match.range(at: 1), in: message)!
            let mention = String(message[mentionRange])
            
            parsedMessage = message.replacingCharacters(in: Range(match.range, in: message)!, with: "")
            parsedMessage = parsedMessage.trimmingCharacters(in: .whitespacesAndNewlines)
            
            switch mention.lowercased() {
            case "a", "claude":
                llmName = "claude"
            case "c", "chatgpt":
                llmName = "chatgpt"
            case "g", "gemini":
                llmName = "gemini"
            case "q":
                llmName = "gemini"
                dataQuery = parsedMessage
                parsedMessage = ""
            default:
                // Check if the mention matches a character name
                if let character = characters.first(where: { $0.character_name.lowercased() == mention.lowercased() }) {
                    llmName = character.llm_name
                } else {
                    llmName = "all"
                }
            }
            return (llmName, parsedMessage, dataQuery)
        }
        
        // Check for character addressing if no @mention was found
        if !characters.isEmpty {
            for character in characters {
                let characterName = character.character_name
                if message.lowercased().hasPrefix(characterName.lowercased() + ",") ||
                   message.lowercased().hasPrefix(characterName.lowercased() + " ") {
                    llmName = character.llm_name
                    let rangeToRemove = message.range(of: characterName, options: [.caseInsensitive])
                    if let rangeToRemove = rangeToRemove {
                        var modifiedMessage = message
                        modifiedMessage.removeSubrange(rangeToRemove)
                        parsedMessage = modifiedMessage.trimmingCharacters(in: CharacterSet(charactersIn: " ,"))
                        return (llmName, parsedMessage, dataQuery)
                    }
                }
            }
        }
        
        return (llmName, parsedMessage, dataQuery)
    }
    
    func getSenderName(for llmName: String, characters: [CharacterModel]) -> String {
        // Check if this LLM has a character assigned
        if let character = characters.first(where: { $0.llm_name == llmName }) {
            return character.character_name
        }
        
        // Otherwise, return the default name
        switch llmName.lowercased() {
        case "gemini":
            return "Gemini"
        case "chatgpt":
            return "ChatGPT"
        case "claude":
            return "Claude"
        case "user":
            return "You"
        case "system":
            return "System"
        default:
            return "Unknown"
        }
    }
    
    func getRecentContext() -> [[String: Any]] {
        let contextMessages = messages.suffix(5)
        return contextMessages.map { message in
            return [
                "id": message.id.uuidString,
                "text": message.text,
                "sender": message.sender,
                "senderName": message.senderName,
                "timestamp": message.timestamp.timeIntervalSince1970,
                "referencedMessageId": message.referencedMessageId?.uuidString as Any,
                "messageIntent": message.messageIntent as Any
            ]
        }
    }
}