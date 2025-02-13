// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/MessageBubble.swift
import SwiftUI

struct MessageBubble: View {
    let message: Message

    var body: some View {
        HStack {
            if message.sender == "User" {
                Spacer()
                VStack(alignment: .trailing) {
                    Text("nick")
                        .font(.caption)
                        .foregroundColor(message.color)
                        .padding(.trailing, 5)
                    Text(message.text)
                        .padding()
                        .background(message.color)
                        .foregroundColor(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
            } else {
                VStack(alignment: .leading) {
                    Text(message.sender)
                        .font(.caption)
                        .foregroundColor(message.color)
                    Text(message.text)
                        .padding()
                        .background(message.color)
                        .foregroundColor(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                Spacer()
            }
        }
    }
}
