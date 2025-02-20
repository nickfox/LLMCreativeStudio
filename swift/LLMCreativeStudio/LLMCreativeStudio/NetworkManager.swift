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

            if let httpResponse = response as? HTTPURLResponse {
                print("HTTP Status Code: \(httpResponse.statusCode)")

                if (200...299).contains(httpResponse.statusCode) {
                    if let data = data,
                       let jsonResponse = try? JSONSerialization.jsonObject(with: data, options: [])
                    {
                        DispatchQueue.main.async { [weak self] in
                            guard let self = self else { return }
                            // Handle the new response format, which can be a single response or an array
                            if let responseDict = jsonResponse as? [String: Any],
                               let responseText = responseDict["response"] as? String,
                               let llmName = responseDict["llm"] as? String {
                                // Single response
                                print("Received llmName from server (single):", llmName)  // Add this line
                                let llmMessage = Message(text: responseText, sender: llmName, senderName: self.getSenderName(for: llmName))
                                self.messages.append(llmMessage)
                            } else if let responseArray = jsonResponse as? [[String: Any]] {
                                // Multiple responses.
                                for responseDict in responseArray {
                                    if let responseText = responseDict["response"] as? String,
                                       let llmName = responseDict["llm"] as? String {
                                        print("Received llmName from server (multiple):", llmName)  // Add this line
                                        let llmMessage = Message(text: responseText, sender: llmName, senderName: self.getSenderName(for: llmName))
                                        self.messages.append(llmMessage)
                                    }
                                }
                            } else {
                                print("Error: Unexpected response format from server.")
                            }
                        }
                    }
                } else { // Handle errors
                    if let data = data,
                          let errorResponse = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
                           print("Error Response from Server:")
                           print(errorResponse)
                       } else if let data = data, let errorString = String(data: data, encoding: .utf8) {
                        print("Error Response from Server:")
                        print(errorString)
                    }
                }
            }
        }
        task.resume()
    }

    // Add this function to add a message directly to the messages array
    func addMessage(text: String, sender: String, senderName: String) {
        DispatchQueue.main.async {
            let newMessage = Message(text: text, sender: sender, senderName: senderName)
            self.messages.append(newMessage)
        }
    }

    func clearMessages() {
        DispatchQueue.main.async {
            self.messages = []
        }
    }
    
    func parseMessage(_ message: String) -> (llmName: String, parsedMessage: String, dataQuery: String) {
        // Regular expressions to find @mentions
        let mentionRegex = try! NSRegularExpression(pattern: "@([a-zA-Z]+)", options: [])
        let matches = mentionRegex.matches(in: message, options: [], range: NSRange(location: 0, length: message.utf16.count))

        var llmName = "all" // Default to all LLMs if no mention
        var dataQuery = ""
        var parsedMessage = message

        if let match = matches.first { // Only consider the *first* mention
            let mentionRange = Range(match.range(at: 1), in: message)!
            let mention = String(message[mentionRange])

            // Remove the mention from the message
            parsedMessage = message.replacingCharacters(in: Range(match.range, in: message)!, with: "")
            parsedMessage = parsedMessage.trimmingCharacters(in: .whitespacesAndNewlines)

            switch mention.lowercased() {
            case "a", "claude":
                llmName = "claude"
            case "c", "chatgpt":
                llmName = "chatgpt"
            case "g", "gemini":
                llmName = "gemini"
            case "q":
                llmName = "gemini"  // Still use Gemini for data queries
                dataQuery = parsedMessage // The rest of the message is the data query
                parsedMessage = "" // The message to the LLM is empty
            default:
                llmName = "all" // Default fallback is all LLMs
            }
        } else {
            //If no mention, then the message is for the user.
            llmName = "all"
            parsedMessage = message
        }

        return (llmName, parsedMessage, dataQuery)
    }


    // Helper function to get color for LLM
    func getSenderName(for llmName: String) -> String {
        switch llmName.lowercased() {
            case "gemini":
                return "Gemini"
            case "chatgpt":
                return "ChatGPT"
            case "claude":
                return "Claude"
            case "user":
                return "nick"
            default:
                return "Unknown"
            }
    }
}
