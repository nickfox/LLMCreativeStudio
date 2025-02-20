// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/Message.swift
import SwiftUI // Import SwiftUI for Color

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let sender: String  // "user", "gemini", "chatgpt", "claude"
    let senderName: String //"nick", "Gemini", "ChatGPT", "Claude"
}
