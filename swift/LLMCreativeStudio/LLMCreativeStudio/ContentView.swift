// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/ContentView.swift

import SwiftUI

struct ContentView: View {
   @State private var messageText: String = ""
   @EnvironmentObject var networkManager: NetworkManager
   @Binding var sessionId: String
   
   var body: some View {
       VStack {
           ScrollView {
               ScrollViewReader { scrollView in
                   VStack(alignment: .leading, spacing: 12) { // Added consistent spacing
                       ForEach(networkManager.messages) { message in
                           MessageBubble(message: message)
                               .id(message.id)
                       }
                   }
                   .padding(.horizontal, 16)
                   .padding(.vertical, 12)
                   .onChange(of: networkManager.messages.count) { oldValue, newValue in
                       withAnimation {
                           scrollView.scrollTo(networkManager.messages.last?.id, anchor: .bottom)
                       }
                   }
               }
           }
           .padding([.top, .leading, .trailing])
           .padding(.trailing, 8) // Extra padding for scrollbar
           
           VStack(alignment: .leading) {
               GrowingTextInput(text: $messageText, onSubmit: sendMessage)
           }
           .padding()
       }
       .background(Color.background)
       .frame(minWidth: 400, minHeight: 600)
   }
   
   func sendMessage() {
       guard !messageText.isEmpty else { return }
       let (llmName, parsedMessage, dataQuery) = networkManager.parseMessage(messageText)
       let senderName = "nick"
       let displayedMessage: String
       
       if llmName == "all" {
           displayedMessage = parsedMessage
       } else if dataQuery.isEmpty {
           displayedMessage = messageText
       } else {
           displayedMessage = parsedMessage
       }
       networkManager.addMessage(text: displayedMessage, sender: "user", senderName: senderName)
       networkManager.sendMessage(message: parsedMessage, llmName: llmName, dataQuery: dataQuery, sessionId: sessionId)
       messageText = ""
   }
}


