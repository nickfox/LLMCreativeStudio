// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/Message.swift

import SwiftUI

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let sender: String  // "user", "gemini", "chatgpt", "claude"
    let senderName: String // "nick", "Gemini", "ChatGPT", "Claude"
    let timestamp: Date
    let referencedMessageId: UUID?  // ID of message being referenced
    let conversationMode: String?    // "open", "debate", "roleplay"
    let messageIntent: String?       // "question", "response", "agreement", "disagreement"
    
    // Date formatter for the specific format you want
    static let timestampFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mma MMM d, yyyy"
        return formatter
    }()
    
    var formattedTimestamp: String {
        let formatted = Message.timestampFormatter.string(from: timestamp)
        return formatted.replacingOccurrences(of: "AM", with: "\u{2009}am ")
                       .replacingOccurrences(of: "PM", with: "\u{2009}pm ")
    }
    
    init(text: String,
         sender: String,
         senderName: String,
         timestamp: Date = Date(),
         referencedMessageId: UUID? = nil,
         conversationMode: String? = nil,
         messageIntent: String? = nil) {
        self.text = text
        self.sender = sender
        self.senderName = senderName
        self.timestamp = timestamp
        self.referencedMessageId = referencedMessageId
        self.conversationMode = conversationMode
        self.messageIntent = messageIntent
    }
}
