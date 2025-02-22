// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/NetworkManager.swift

import Foundation
import Combine
import SwiftUI

class NetworkManager: ObservableObject {
    @Published var messages: [Message] = []
    @Published var currentConversationMode: String = "open"
    
    func sendMessage(message: String, llmName: String, dataQuery: String = "", sessionId: String) {
        guard let url = URL(string: "http://localhost:8000/chat") else {
            print("Invalid URL")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let lastMessageId = messages.last?.id
        
        let json: [String: Any] = [
            "llm_name": llmName,
            "message": message,
            "data_query": dataQuery,
            "session_id": sessionId,
            "conversation_mode": currentConversationMode,
            "referenced_message_id": lastMessageId?.uuidString as Any,
            "context": getRecentContext()
        ]

        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            if let jsonString = String(data: jsonData, encoding: .utf8) {
                print("Sending JSON payload:")
                print(jsonString)
            }
            request.httpBody = jsonData
        } catch {
            print("Error serializing JSON: \(error)")
            return
        }

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error: \(error)")
                return
            }

            if let httpResponse = response as? HTTPURLResponse {
                print("HTTP Status Code: \(httpResponse.statusCode)")

                if (200...299).contains(httpResponse.statusCode) {
                    if let data = data {
                        print("Received raw response from server:")
                        print(String(data: data, encoding: .utf8) ?? "Could not decode response")
                        
                        if let jsonResponse = try? JSONSerialization.jsonObject(with: data, options: []) {
                            print("Parsed JSON response type: \(type(of: jsonResponse))")
                            print("Parsed JSON response content: \(jsonResponse)")
                            
                            DispatchQueue.main.async { [weak self] in
                                guard let self = self else { return }
                                print("Current messages count before processing: \(self.messages.count)")
                                
                                if let responseDict = jsonResponse as? [String: Any],
                                   let responseText = responseDict["response"] as? String,
                                   let llmName = responseDict["llm"] as? String {
                                    print("Processing single response from \(llmName)")
                                    let llmMessage = Message(
                                        text: responseText,
                                        sender: llmName,
                                        senderName: self.getSenderName(for: llmName),
                                        timestamp: Date()
                                    )
                                    self.messages.append(llmMessage)
                                } else if let responseArray = jsonResponse as? [[String: Any]] {
                                    print("Processing array of \(responseArray.count) responses")
                                    for responseDict in responseArray {
                                        if let responseText = responseDict["response"] as? String,
                                           let llmName = responseDict["llm"] as? String {
                                            print("Processing array response from \(llmName)")
                                            let llmMessage = Message(
                                                text: responseText,
                                                sender: llmName,
                                                senderName: self.getSenderName(for: llmName),
                                                timestamp: Date()
                                            )
                                            self.messages.append(llmMessage)
                                        }
                                    }
                                }
                                print("Current messages count after processing: \(self.messages.count)")
                            }
                        } else {
                            print("Failed to parse JSON response")
                        }
                    }
                } else {
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
    
    private func getRecentContext() -> [[String: Any]] {
        let contextMessages = messages.suffix(5)
        return contextMessages.map { message in
            return [
                "id": message.id.uuidString,
                "text": message.text,
                "sender": message.sender,
                "senderName": message.senderName,
                "timestamp": message.timestamp.timeIntervalSince1970,
                "referencedMessageId": message.referencedMessageId?.uuidString as Any,
                "messageIntent": message.messageIntent as Any
            ]
        }
    }

    func addMessage(text: String, sender: String, senderName: String, referencedMessageId: UUID? = nil, messageIntent: String? = nil) {
        DispatchQueue.main.async {
            let newMessage = Message(
                text: text,
                sender: sender,
                senderName: senderName,
                referencedMessageId: referencedMessageId,
                conversationMode: self.currentConversationMode,
                messageIntent: messageIntent
            )
            self.messages.append(newMessage)
        }
    }

    func clearMessages() {
        DispatchQueue.main.async {
            self.messages = []
        }
    }
    
    func parseMessage(_ message: String) -> (llmName: String, parsedMessage: String, dataQuery: String) {
        let mentionRegex = try! NSRegularExpression(pattern: "@([a-zA-Z]+)", options: [])
        let matches = mentionRegex.matches(in: message, options: [], range: NSRange(location: 0, length: message.utf16.count))

        var llmName = "all"
        var dataQuery = ""
        var parsedMessage = message

        if let match = matches.first {
            let mentionRange = Range(match.range(at: 1), in: message)!
            let mention = String(message[mentionRange])

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
                llmName = "gemini"
                dataQuery = parsedMessage
                parsedMessage = ""
            default:
                llmName = "all"
            }
        } else {
            llmName = "all"
            parsedMessage = message
        }

        return (llmName, parsedMessage, dataQuery)
    }

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
