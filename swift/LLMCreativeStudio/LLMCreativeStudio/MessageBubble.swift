// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/MessageBubble.swift

import SwiftUI

struct MessageBubble: View {
    let message: Message
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 8) {
                // Sender name with color coding
                Text(message.senderName)
                    .foregroundColor(getSenderColor())
                    .font(.system(size: 13, weight: .medium))
                
                // Show debate round indicator if available
                if let round = message.debateRound, round > 0 {
                    Text(getDebateRoundName(round: round))
                        .font(.system(size: 11))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.2))
                        .cornerRadius(4)
                }
                
                // Show waiting for input indicator
                if message.waitingForUser == true {
                    Text("Waiting for your input")
                        .font(.system(size: 11))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.orange.opacity(0.3))
                        .foregroundColor(Color.orange)
                        .cornerRadius(4)
                }
                
                Spacer()
                
                Text(message.formattedTimestamp)
                    .foregroundColor(.gray.opacity(0.5))
                    .font(.system(size: 11))
            }
            .padding(.bottom, 2)
            .padding(.horizontal, 16)
            
            // Message content with special styling for different types
            VStack(alignment: .leading, spacing: 8) {
                // Show special debate info header for system messages
                if message.sender == "system" && message.debateState != nil {
                    if message.waitingForUser == true {
                        Text("Your turn - add your perspective or use /continue to skip")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.orange)
                            .padding(.bottom, 4)
                            .textSelection(.enabled)
                    }
                }
                
                // The actual message text
                Text(message.text)
                    .font(.system(size: 15))
                    .foregroundColor(.messageText.opacity(0.9))
                    .textSelection(.enabled)  // Enable text selection
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(getMessageBackground())
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(message.waitingForUser == true ? Color.orange.opacity(0.5) : Color.clear, lineWidth: 1)
            )
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }
    
    // Helper function to get color for sender name
    private func getSenderColor() -> Color {
        switch message.sender {
        case "user":
            return Color(red: 0.0, green: 0.8, blue: 1.0, opacity: 0.7)    // Cyan for user
        case "system":
            return Color.orange.opacity(0.8)                               // Orange for system
        case "synthesis":
            return Color.purple.opacity(0.8)                               // Purple for synthesis
        default:
            return Color(red: 1.0, green: 0.2, blue: 0.7, opacity: 0.5)   // Magenta for LLMs
        }
    }
    
    // Helper function to get background color for message bubble
    private func getMessageBackground() -> Color {
        if message.waitingForUser == true {
            return Color.orange.opacity(0.05)  // Light orange for user input prompt
        } else if message.debateState?.contains("SYNTHESIS") == true {
            return Color.purple.opacity(0.05)  // Light purple for synthesis
        } else {
            return Color(NSColor.windowBackgroundColor).opacity(0.17)  // Default
        }
    }
    
    // Helper function to get debate round name
    private func getDebateRoundName(round: Int) -> String {
        switch round {
        case 1: return "Opening"
        case 2: return "Questions"
        case 3: return "Responses"
        case 4: return "Consensus"
        case 5: return "Synthesis"
        default: return "Round \(round)"
        }
    }
}
