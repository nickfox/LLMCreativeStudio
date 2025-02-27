// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/ContentView.swift

import SwiftUI
import AppKit

struct ContentView: View {
   @State private var messageText: String = ""
   @EnvironmentObject var networkManager: NetworkManager
   @State private var selectedTab = 0
   @State private var isShowingConversationOptions = false
   @State private var debatePromptShowing = false
   
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
           
           // Files Tab
           FileUploadView()
               .tabItem {
                   Label("Files", systemImage: "doc.fill")
               }
               .tag(2)
           
           // Characters Tab
           CharacterView()
               .tabItem {
                   Label("Characters", systemImage: "person.2")
               }
               .tag(3)
       }
       .frame(minWidth: 800, minHeight: 600)
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
               
               HStack(spacing: 12) {
                   // Active debate indicator
                   if isActiveDebate() {
                       DebateStatusView(networkManager: networkManager)
                   }
                   
                   // Conversation mode display
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
                   ZStack {
                       // Full-width background that fills entire scroll area
                       Color(NSColor.windowBackgroundColor)
                           .ignoresSafeArea()
                       
                       // Messages container
                       VStack(alignment: .leading, spacing: 12) {
                           ForEach(networkManager.messages) { message in
                               MessageBubble(message: message)
                                   .id(message.id)
                           }
                           
                           // Spacer to push content to the top when there are few messages
                           if !networkManager.messages.isEmpty {
                               Spacer(minLength: 20)
                           }
                       }
                       .padding(.horizontal, 16)
                       .padding(.vertical, 12)
                       .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity, alignment: .leading)
                   }
                   .onChange(of: networkManager.messages.count) { _, _ in
                       withAnimation {
                           scrollView.scrollTo(networkManager.messages.last?.id, anchor: .bottom)
                       }
                   }
               }
           }
           .background(Color(NSColor.windowBackgroundColor))
           .padding([.top, .leading, .trailing])
           .padding(.trailing, 8) // Extra padding for scrollbar
           
           VStack(alignment: .leading, spacing: 0) {
               // Show debate prompt banner when system is waiting for user input
               if isWaitingForDebateInput() {
                   DebateInputPromptView(continueAction: {
                       // Send the /continue command
                       messageText = "/continue"
                       sendMessage()
                   })
               }
               
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
   
   // Helper function to check if we're in an active debate
   func isActiveDebate() -> Bool {
       // Check the last few messages for debate indicators
       let recentMessages = networkManager.messages.suffix(10)
       for message in recentMessages.reversed() {
           if message.debateRound != nil || message.debateState != nil {
               return true
           }
       }
       return false
   }
   
   // Helper function to check if the system is waiting for user input in a debate
   func isWaitingForDebateInput() -> Bool {
       // Check the most recent messages
       let recentMessages = networkManager.messages.suffix(5)
       for message in recentMessages.reversed() {
           if message.waitingForUser == true {
               return true
           }
       }
       return false
   }
}

struct CharacterIndicator: View {
    let character: CharacterModel
    
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

// Debate Status View Component
struct DebateStatusView: View {
    @ObservedObject var networkManager: NetworkManager
    
    var body: some View {
        // Determine current debate status
        let status = getCurrentDebateStatus()
        
        HStack(spacing: 6) {
            Circle()
                .fill(Color.orange)
                .frame(width: 8, height: 8)
            
            Text("Debate: \(status.round) | \(status.state)")
                .font(.caption)
                .foregroundColor(.secondary)
                .textSelection(.enabled)
        }
        .padding(.vertical, 4)
        .padding(.horizontal, 8)
        .background(Color.orange.opacity(0.1))
        .cornerRadius(12)
    }
    
    // Get current debate round and state from messages
    func getCurrentDebateStatus() -> (round: String, state: String) {
        // Default values
        var currentRound = "Active"
        var currentState = "In Progress"
        
        // Search for most recent debate indicators
        for message in networkManager.messages.reversed() {
            if let round = message.debateRound, let _ = message.debateState {
                switch round {
                case 1: currentRound = "Opening"
                case 2: currentRound = "Questions"
                case 3: currentRound = "Responses"
                case 4: currentRound = "Consensus"
                case 5: currentRound = "Synthesis"
                default: currentRound = "Round \(round)"
                }
                
                if message.waitingForUser == true {
                    currentState = "Waiting for you"
                } else {
                    currentState = "In progress"
                }
                
                break
            }
        }
        
        return (round: currentRound, state: currentState)
    }
}

// Debate input prompt view shown when user input is required
struct DebateInputPromptView: View {
    let continueAction: () -> Void
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Your turn in the debate")
                    .font(.headline)
                    .foregroundColor(.orange)
                    .textSelection(.enabled)
                
                Text("Add your thoughts or use /continue to skip")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .textSelection(.enabled)
            }
            
            Spacer()
            
            Button(action: continueAction) {
                HStack {
                    Text("Continue")
                    Image(systemName: "arrow.right.circle.fill")
                }
                .font(.callout)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.orange.opacity(0.1))
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding()
        .background(Color.orange.opacity(0.05))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.orange.opacity(0.3), lineWidth: 1)
        )
        .cornerRadius(8)
        .padding(.bottom, 8)
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


