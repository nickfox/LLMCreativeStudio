// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/ContentView.swift
import SwiftUI

struct ContentView: View {
    @State private var messageText: String = ""
    @State private var selectedLLM: String = "Gemini"
    let llms = ["Gemini", "ChatGPT", "Claude"]

    @State private var useDataQuery: Bool = false
    @State private var dataQueryText: String = ""
    
    @State private var sessionId: String = UUID().uuidString //Unique session ID

    @ObservedObject var networkManager = NetworkManager() // Use the NetworkManager

    var body: some View {
        VStack {
            // Chat History Display (Scrollable message bubbles)
            ScrollView {
                ScrollViewReader { scrollView in
                    VStack(alignment: .leading) {
                        ForEach(networkManager.messages) { message in // Get messages from NetworkManager
                            MessageBubble(message: message)
                                .id(message.id)
                        }
                    }
                    .onChange(of: networkManager.messages.count) { oldValue, newValue in
                        withAnimation {
                            scrollView.scrollTo(networkManager.messages.last?.id, anchor: .bottom)
                        }
                    }
                }
            }
            .padding([.top, .leading, .trailing])

            // Message Input and Controls
            VStack(alignment: .leading) {
                Text("Selected LLM: \(selectedLLM)")
                    .font(.caption)
                    .padding(.leading)

                HStack {
                    Picker("LLM:", selection: $selectedLLM) {
                        ForEach(llms, id: \.self) { llm in
                            Text(llm)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .frame(maxWidth: 250)
                }

                Toggle(isOn: $useDataQuery) {
                    Text("Use Data Query")
                }.padding(.leading)

                if useDataQuery {
                    TextField("Enter data query", text: $dataQueryText)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .padding(.bottom)
                }

                HStack {
                    TextField("Enter your message", text: $messageText)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .onSubmit {
                            sendMessage()
                        }

                    Button("Send") {
                        sendMessage()
                    }
                    .keyboardShortcut(.defaultAction)
                }
                HStack {
                    Button("Clear History") { //Add a clear history button
                        clearHistory()
                    }
                }
            }
            .padding()
        }
    }

    func sendMessage() {
        guard !messageText.isEmpty else { return }

        // Add user message *locally* before sending
        networkManager.addMessage(text: messageText, sender: "User") // Add to NM's messages

        networkManager.sendMessage(message: messageText, llmName: selectedLLM, dataQuery: useDataQuery ? dataQueryText : "", sessionId: sessionId)

        messageText = "" // Clear the input field
        if useDataQuery {
            dataQueryText = ""
        }
    }
    
    func clearHistory() {
        networkManager.clearMessages()
        sessionId = UUID().uuidString // Generate a new session ID
    }
}