// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/MessageBubble.swift

import SwiftUI

struct MessageBubble: View {
    let message: Message
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(message.senderName)
                    .foregroundColor(message.sender == "user" ?
                        Color(red: 0.0, green: 0.8, blue: 1.0, opacity: 0.7) :     // Cyan for user
                        Color(red: 1.0, green: 0.2, blue: 0.7, opacity: 0.5))      // Magenta for LLMs
                    .font(.system(size: 13, weight: .medium))
                
                Spacer()
                
                Text(message.formattedTimestamp)
                    .foregroundColor(.gray.opacity(0.5))
                    .font(.system(size: 11))
            }
            .padding(.bottom, 2)
            .padding(.horizontal, 16)
            
            Text(message.text)
                .font(.system(size: 15))
                .foregroundColor(.messageText.opacity(0.9))
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(NSColor.windowBackgroundColor).opacity(0.17))
                .cornerRadius(12)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }
}
