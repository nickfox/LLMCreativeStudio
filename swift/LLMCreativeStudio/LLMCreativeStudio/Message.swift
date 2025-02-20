// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/Message.swift
import SwiftUI

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let sender: String  // "user", "gemini", "chatgpt", "claude"
    let senderName: String //"nick", "Gemini", "ChatGPT", "Claude"
    let timestamp: Date
    
    // Date formatter for the specific format you want
    static let timestampFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mma MMM d, yyyy"
        return formatter
    }()
    
    var formattedTimestamp: String {
        let formatted = Message.timestampFormatter.string(from: timestamp)
            return formatted.replacingOccurrences(of: "AM", with: "am")
                           .replacingOccurrences(of: "PM", with: "pm")
    }
}
