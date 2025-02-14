// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/NetworkManager.swift

import Foundation
import Combine
import SwiftUI // Import SwiftUI for Color

class NetworkManager: ObservableObject {
    @Published var messages: [Message] = [] // Store messages here

    func sendMessage(message: String, llmName: String, dataQuery: String = "", sessionId: String) {
        guard let url = URL(string: "http://localhost:8000/chat") else {
            print("Invalid URL")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let json: [String: Any] = ["llm_name": llmName, "message": message, "data_query": dataQuery, "session_id": sessionId] // Include session ID

        // *** PRINT THE JSON PAYLOAD ***
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            if let jsonString = String(data: jsonData, encoding: .utf8) {
                print("Sending JSON payload:")
                print(jsonString)
            }
            request.httpBody = jsonData // Set body *after* printing
        } catch {
            print("Error serializing JSON: \(error)")
            return  // Don't send if JSON is bad
        }

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error: \(error)")
                return
            }

            if let httpResponse = response as? HTTPURLResponse { // No guard needed
                print("HTTP Status Code: \(httpResponse.statusCode)") // Always print status

                if (200...299).contains(httpResponse.statusCode) {
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
                } else { // Handle errors
                    if let data = data,
                          let errorResponse = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
                           print("Error Response from Server:")
                           print(errorResponse)
                       } else if let data = data, let errorString = String(data: data, encoding: .utf8) {
                            print("Error Response from Server:")
                            print(errorString) // Print raw error string
                        }
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

    func clearMessages() {
        DispatchQueue.main.async {
            self.messages = []
        }
    }

    // Helper function to get color for LLM
    func llmColor(for llmName: String) -> Color {
        return .gray
    }
}
