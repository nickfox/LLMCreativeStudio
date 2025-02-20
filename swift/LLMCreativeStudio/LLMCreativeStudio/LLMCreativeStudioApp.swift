// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/LLMCreativeStudioApp.swift
import SwiftUI

@main
struct LLMCreativeStudioApp: App {
    @StateObject private var networkManager = NetworkManager() // Create it here.
    @State private var sessionId: String = UUID().uuidString

    var body: some Scene {
        WindowGroup {
            ContentView(sessionId: $sessionId) // Pass sessionId
                .environmentObject(networkManager) // Inject NetworkManager
                .background(Color.background) // Set the background color
                .frame(minWidth: 400, minHeight: 600)
                .onAppear {
                    NSWindow.allowsAutomaticWindowTabbing = false // Optional
                }
        }
        .commands {  // Add the menu commands here
            CommandGroup(replacing: .newItem) {
                // We'll leave the "New Window" command alone, but you could
                // customize it if you wanted.
            }
            CommandGroup(replacing: .undoRedo) {} //Remove undo/redo
            CommandGroup(replacing: .pasteboard) {} // Remove cut/copy/paste/delete
            CommandMenu("Chat") { // Add a "Chat" menu
                Button("Clear History") {
                    networkManager.clearMessages()
                    sessionId = UUID().uuidString
                }
                .keyboardShortcut("k", modifiers: [.command]) // Optional shortcut
            }
        }
    }
}

// --- Color Definitions ---
extension Color {
    static let background = Color(hex: "1A1A1D")     // Rich dark charcoal
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
