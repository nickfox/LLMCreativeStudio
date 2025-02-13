// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/NetworkManager.swift

import Foundation
import Combine
import SwiftUI // Import SwiftUI for Color

class NetworkManager: ObservableObject {
    @Published var messages: [Message] = [] // Store messages here

    func sendMessage(message: String, llmName: String, dataQuery: String = "") {
        guard let url = URL(string: "http://localhost:8000/chat") else {
            print("Invalid URL")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let json: [String: Any] = ["llm_name": llmName, "message": message, "data_query": dataQuery]
        let jsonData = try? JSONSerialization.data(withJSONObject: json)
        request.httpBody = jsonData

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error: \(error)")
                return
            }

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                print("Server error")
                return
            }

            if let data = data,
               let jsonResponse = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
               let responseText = jsonResponse["response"] as? String,
               let llmName = jsonResponse["llm"] as? String
            {
                DispatchQueue.main.async {
                    //Append to NetworkManagers messages array.
                    let llmMessage = Message(text: responseText, sender: llmName, color: self.llmColor(for: llmName))
                    self.messages.append(llmMessage)
                }
            }
        }
        task.resume()
    }
    
    // Add this function to add a message directly to the messages array
    func addMessage(text: String, sender: String) {
        DispatchQueue.main.async {
            let newMessage = Message(text: text, sender: sender, color: self.llmColor(for: sender))
            self.messages.append(newMessage)
        }
    }

    // Helper function to get color for LLM
    func llmColor(for llmName: String) -> Color {
        switch llmName.lowercased() {
        case "gemini":
            return .green
        case "chatgpt":
            return .orange
        case "claude":
            return .purple
        case "user":
            return .blue
        default:
            return .gray
        }
    }
}
