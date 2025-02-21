// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/GrowingTextInput.swift

import SwiftUI
import AppKit

struct GrowingTextInput: View {
    @Binding var text: String
    let onSubmit: () -> Void
    @State private var textEditorHeight: CGFloat = 40
    
    var body: some View {
        TextEditor(text: $text)
            .scrollContentBackground(.hidden)
            .scrollDisabled(true)
            .background(.clear)
            .frame(height: textEditorHeight)
            .padding(12)
            .background(Color.messageBubble)
            .foregroundColor(.messageText)
            .font(.system(size: 15))
            .cornerRadius(10)
            .onChange(of: text) {_, newText in
                // Simpler height calculation based on line count
                let lineCount = newText.components(separatedBy: .newlines).count
                textEditorHeight = min(max(40, CGFloat(lineCount * 20)), 120)
            }
            .onKeyPress(.return, phases: .down) { keyPress in
                if !keyPress.modifiers.contains(.shift) {
                    onSubmit()
                    return .handled
                }
                return .ignored
            }
    }
}
