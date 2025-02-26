import Foundation

func testParseMessage() {
    let networkManager = NetworkManager()
    
    // Test @c
    let result = networkManager.parseMessage("@c What do you think?")
    print("@c maps to: \(result.llmName)")
    
    // Expected: now maps to claude instead of chatgpt
    if result.llmName == "claude" {
        print("Test passed: @c maps to claude ✅")
    } else {
        print("Test failed: @c maps to \(result.llmName) ❌")
    }
}

// Stub NetworkManager implementation to test the parseMessage method
class NetworkManager {
    func parseMessage(_ message: String) -> (llmName: String, parsedMessage: String, dataQuery: String) {
        let mentionRegex = try\! NSRegularExpression(pattern: "@([a-zA-Z]+)", options: [])
        let matches = mentionRegex.matches(in: message, options: [], range: NSRange(location: 0, length: message.utf16.count))

        var llmName = "all"
        var dataQuery = ""
        var parsedMessage = message

        if let match = matches.first {
            let mentionRange = Range(match.range(at: 1), in: message)\!
            let mention = String(message[mentionRange])

            parsedMessage = message.replacingCharacters(in: Range(match.range, in: message)\!, with: "")
            parsedMessage = parsedMessage.trimmingCharacters(in: .whitespacesAndNewlines)

            switch mention.lowercased() {
            case "a", "claude":
                llmName = "claude"
            case "c": // Changed from "chatgpt" to "claude" 
                llmName = "claude"
            case "chatgpt":
                llmName = "chatgpt"
            case "g", "gemini":
                llmName = "gemini"
            case "q":
                llmName = "gemini"
                dataQuery = parsedMessage
                parsedMessage = ""
            default:
                llmName = "all"
            }
        }

        return (llmName, parsedMessage, dataQuery)
    }
}

testParseMessage()
