// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/LLMCreativeStudioApp.swift

import SwiftUI

@main
struct LLMCreativeStudioApp: App {
    @StateObject private var networkManager = NetworkManager() // Create it here.

    var body: some Scene {
        WindowGroup {
            ContentView() // No need to pass sessionId
                .environmentObject(networkManager) // Inject NetworkManager
                .onAppear {
                    NSWindow.allowsAutomaticWindowTabbing = false // Optional
                }
        }
        .commands {  // Add the menu commands here
            CommandGroup(replacing: .newItem) {
                Button("New Project") {
                    // This will be handled by the ProjectView
                }
                .keyboardShortcut("n", modifiers: [.command])
                
                Button("Open Project") {
                    // This will be handled by the ProjectView
                }
                .keyboardShortcut("o", modifiers: [.command])
            }
            CommandMenu("Session") { // Add a Session menu
                Button("Clear Chat History") {
                    networkManager.clearMessages()
                }
                .keyboardShortcut("k", modifiers: [.command]) // Optional shortcut
                
                Divider()
                
                Button("Switch to Chat") {
                    // Find a way to switch to the Chat tab
                }
                .keyboardShortcut("1", modifiers: [.command])
                
                Button("Switch to Projects") {
                    // Find a way to switch to the Projects tab
                }
                .keyboardShortcut("2", modifiers: [.command])
                
                Button("Switch to Characters") {
                    // Find a way to switch to the Characters tab
                }
                .keyboardShortcut("3", modifiers: [.command])
            }
        }
    }
}

// --- Color Definitions ---
extension Color {
    static let background = Color(hex: "222225")     // Rich dark charcoal (slightly adjusted)
    static let messageBubble = Color(hex: "2C2C30")  // Slightly lighter charcoal
    static let messageText = Color(hex: "F5F5F5")    // Soft white
    static let senderName = Color(hex: "E065BA")     // Muted magenta
}

// Hex color helper
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

