// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/Message.swift

import SwiftUI

public struct Message: Identifiable {
    public let id = UUID()
    public let text: String
    public let sender: String  // "user", "gemini", "chatgpt", "claude", "system", "synthesis"
    public let senderName: String // "nick", "Gemini", "ChatGPT", "Claude", "System", "Synthesis"
    public let timestamp: Date
    public let referencedMessageId: UUID?  // ID of message being referenced
    public let conversationMode: String?    // "open", "debate", "creative", "research"
    public let messageIntent: String?       // "question", "response", "agreement", "disagreement"
    
    // Debate specific properties
    public let debateRound: Int?           // 1=Opening, 2=Questioning, 3=Responses, 4=Consensus, 5=Synthesis
    public let debateState: String?        // Corresponds to DebateState enum names
    public let waitingForUser: Bool?       // Indicates if waiting for user input
    public let actionRequired: String?     // E.g., "debate_input" - UI action needed
    
    // Date formatter for the specific format you want
    public static let timestampFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mma MMM d, yyyy"
        return formatter
    }()
    
    public var formattedTimestamp: String {
        let formatted = Message.timestampFormatter.string(from: timestamp)
        return formatted.replacingOccurrences(of: "AM", with: "\u{2009}am ")
                       .replacingOccurrences(of: "PM", with: "\u{2009}pm ")
    }
    
    public init(text: String,
         sender: String,
         senderName: String,
         timestamp: Date = Date(),
         referencedMessageId: UUID? = nil,
         conversationMode: String? = nil,
         messageIntent: String? = nil,
         debateRound: Int? = nil,
         debateState: String? = nil,
         waitingForUser: Bool? = nil,
         actionRequired: String? = nil) {
        self.text = text
        self.sender = sender
        self.senderName = senderName
        self.timestamp = timestamp
        self.referencedMessageId = referencedMessageId
        self.conversationMode = conversationMode
        self.messageIntent = messageIntent
        self.debateRound = debateRound
        self.debateState = debateState
        self.waitingForUser = waitingForUser
        self.actionRequired = actionRequired
    }
}
