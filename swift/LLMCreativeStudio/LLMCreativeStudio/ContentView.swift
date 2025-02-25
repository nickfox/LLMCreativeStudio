// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/ContentView.swift

import SwiftUI
import AppKit

struct ContentView: View {
   @State private var messageText: String = ""
   @EnvironmentObject var networkManager: NetworkManager
   @State private var selectedTab = 0
   @State private var isShowingConversationOptions = false
   
   var body: some View {
       TabView(selection: $selectedTab) {
           // Chat Tab
           chatView
               .tabItem {
                   Label("Chat", systemImage: "bubble.left.and.bubble.right")
               }
               .tag(0)
           
           // Projects Tab
           ProjectView()
               .tabItem {
                   Label("Projects", systemImage: "folder")
               }
               .tag(1)
           
           // Characters Tab
           CharacterView()
               .tabItem {
                   Label("Characters", systemImage: "person.2")
               }
               .tag(2)
       }
       .frame(minWidth: 700, minHeight: 600)
   }
   
   private var chatView: some View {
       VStack {
           // Project and Mode Info Bar
           HStack {
               if let project = networkManager.currentProject {
                   HStack {
                       Text(project.name)
                           .font(.headline)
                       
                       Text("•")
                           .foregroundColor(.secondary)
                       
                       Text(project.type.capitalized)
                           .font(.subheadline)
                           .foregroundColor(.secondary)
                   }
               } else {
                   Text("No Project Selected")
                       .font(.subheadline)
                       .foregroundColor(.secondary)
               }
               
               Spacer()
               
               HStack {
                   Text("Mode: \(networkManager.currentConversationMode.capitalized)")
                       .font(.subheadline)
                   
                   Button(action: {
                       isShowingConversationOptions = true
                   }) {
                       Image(systemName: "gear")
                   }
               }
           }
           .padding(.horizontal)
           .padding(.vertical, 8)
           .background(Color(NSColor.windowBackgroundColor))
           
           // Character Indicators (if any)
           if !networkManager.characters.isEmpty {
               ScrollView(.horizontal, showsIndicators: false) {
                   HStack(spacing: 12) {
                       ForEach(networkManager.characters) { character in
                           CharacterIndicator(character: character)
                       }
                   }
                   .padding(.horizontal)
               }
               .padding(.vertical, 8)
               .background(Color(NSColor.windowBackgroundColor).opacity(0.5))
           }
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
           .background(Color.background)
           .padding([.top, .leading, .trailing])
           .padding(.trailing, 8) // Extra padding for scrollbar
           
           VStack(alignment: .leading) {
               GrowingTextInput(text: $messageText, onSubmit: sendMessage)
           }
           .padding()
       }
       .popover(isPresented: $isShowingConversationOptions) {
           ConversationOptionsView()
               .frame(width: 300, height: 350)
       }
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
       networkManager.sendMessage(message: parsedMessage, llmName: llmName, dataQuery: dataQuery, sessionId: networkManager.sessionId)
       messageText = ""
   }
}

struct CharacterIndicator: View {
    let character: Character
    
    var body: some View {
        HStack {
            Circle()
                .fill(getLLMColor(for: character.llm_name))
                .frame(width: 10, height: 10)
            
            Text(character.character_name)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.vertical, 4)
        .padding(.horizontal, 8)
        .background(getLLMColor(for: character.llm_name).opacity(0.1))
        .cornerRadius(12)
    }
    
    private func getLLMColor(for llmName: String) -> Color {
        switch llmName.lowercased() {
        case "claude":
            return .purple
        case "chatgpt":
            return .green
        case "gemini":
            return .blue
        default:
            return .gray
        }
    }
}

struct ConversationOptionsView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @Environment(\.dismiss) private var dismiss
    @State private var selectedMode: String
    
    init() {
        // Initialize state with the current mode
        _selectedMode = State(initialValue: "open")
    }
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Conversation Mode") {
                    Picker("Mode", selection: $selectedMode) {
                        Text("Open Conversation").tag("open")
                        Text("Debate").tag("debate")
                        Text("Creative").tag("creative")
                        Text("Research").tag("research")
                    }
                    .pickerStyle(.inline)
                    .onChange(of: selectedMode) { oldValue, newValue in
                        if oldValue != newValue {
                            networkManager.currentConversationMode = newValue
                            
                            // Send mode change command to server
                            let modeCommand = "/mode \(newValue)"
                            networkManager.sendMessage(
                                message: modeCommand,
                                llmName: "system",
                                dataQuery: "",
                                sessionId: networkManager.sessionId
                            )
                        }
                    }
                }
                
                Section {
                    Button("Clear Conversation", role: .destructive) {
                        networkManager.clearMessages()
                        dismiss()
                    }
                }
            }
            .navigationTitle("Conversation Options")
            .onAppear {
                selectedMode = networkManager.currentConversationMode
            }
        }
    }
}


