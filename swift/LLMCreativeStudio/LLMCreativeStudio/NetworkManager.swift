// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/NetworkManager.swift

import Foundation
import Combine
import SwiftUI

struct Project: Identifiable, Codable {
    let id: String
    let name: String
    let type: String
    let description: String
    let created_at: String
    let updated_at: String
    
    enum CodingKeys: String, CodingKey {
        case id, name, type, description, created_at, updated_at
    }
}

struct Character: Identifiable, Codable {
    let id: String
    let character_name: String
    let llm_name: String
    let background: String
    let created_at: String
    
    enum CodingKeys: String, CodingKey {
        case id, character_name, llm_name, background, created_at
    }
}

struct ProjectFile: Identifiable, Codable {
    let id: String
    let file_path: String
    let file_type: String
    let description: String
    let is_reference: Bool
    let is_output: Bool
    let created_at: String
    
    enum CodingKeys: String, CodingKey {
        case id, file_path, file_type, description, is_reference, is_output, created_at
    }
}

class NetworkManager: ObservableObject {
    @Published var messages: [Message] = []
    @Published var currentConversationMode: String = "open"
    @Published var projects: [Project] = []
    @Published var currentProject: Project? = nil
    @Published var characters: [Character] = []
    @Published var files: [ProjectFile] = []
    @Published var isLoading: Bool = false
    @Published var sessionId: String = UUID().uuidString
    
    private let baseURL = "http://localhost:8000"
    
    func sendMessage(message: String, llmName: String, dataQuery: String = "", sessionId: String) {
        guard let url = URL(string: "\(baseURL)/chat") else {
            print("Invalid URL")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let lastMessageId = messages.last?.id
        
        var json: [String: Any] = [
            "llm_name": llmName,
            "message": message,
            "data_query": dataQuery,
            "session_id": sessionId,
            "conversation_mode": currentConversationMode,
            "referenced_message_id": lastMessageId?.uuidString as Any,
            "context": getRecentContext()
        ]
        
        // Add project ID if one is selected
        if let projectId = currentProject?.id {
            json["project_id"] = projectId
        }

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
    
    func getRecentContext() -> [[String: Any]] {
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
                // Check if the mention matches a character name
                if let character = characters.first(where: { $0.character_name.lowercased() == mention.lowercased() }) {
                    llmName = character.llm_name
                } else {
                    llmName = "all"
                }
            }
        } else if currentProject != nil && !characters.isEmpty {
            // Check if the message begins with a character name
            for character in characters {
                let characterName = character.character_name
                if message.lowercased().hasPrefix(characterName.lowercased() + ",") ||
                   message.lowercased().hasPrefix(characterName.lowercased() + " ") {
                    llmName = character.llm_name
                    let rangeToRemove = message.range(of: characterName, options: [.caseInsensitive])
                    if let rangeToRemove = rangeToRemove {
                        var modifiedMessage = message
                        modifiedMessage.removeSubrange(rangeToRemove)
                        parsedMessage = modifiedMessage.trimmingCharacters(in: CharacterSet(charactersIn: " ,"))
                        break
                    }
                }
            }
        }

        return (llmName, parsedMessage, dataQuery)
    }

    func getSenderName(for llmName: String) -> String {
        // Check if this LLM has a character assigned
        if let character = characters.first(where: { $0.llm_name == llmName }) {
            return character.character_name
        }
        
        // Otherwise, return the default name
        switch llmName.lowercased() {
        case "gemini":
            return "Gemini"
        case "chatgpt":
            return "ChatGPT"
        case "claude":
            return "Claude"
        case "user":
            return "nick"
        case "system":
            return "System"
        default:
            return "Unknown"
        }
    }
    
    // Methods for Project Management
    
    func fetchProjects(completion: ((Error?) -> Void)? = nil) {
        isLoading = true
        guard let url = URL(string: "\(baseURL)/projects") else {
            print("Invalid URL")
            isLoading = false
            completion?(NSError(domain: "Invalid URL", code: 0, userInfo: nil))
            return
        }
        
        let task = URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                if let error = error {
                    print("Error fetching projects: \(error)")
                    completion?(error)
                    return
                }
                
                guard let data = data else {
                    print("No data received")
                    completion?(NSError(domain: "No data received", code: 0, userInfo: nil))
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let projectsData = json["projects"] as? [[String: Any]] {
                        let decoder = JSONDecoder()
                        let projectsData = try JSONSerialization.data(withJSONObject: projectsData, options: [])
                        let projects = try decoder.decode([Project].self, from: projectsData)
                        self?.projects = projects
                        completion?(nil)
                    }
                } catch {
                    print("Error parsing projects: \(error)")
                    completion?(error)
                }
            }
        }
        task.resume()
    }
    
    func createProject(name: String, type: String, description: String, completion: @escaping (Result<String, Error>) -> Void) {
        isLoading = true
        guard let url = URL(string: "\(baseURL)/projects") else {
            isLoading = false
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let json: [String: Any] = [
            "name": name,
            "type": type,
            "description": description,
            "metadata": [String: String]()
        ]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            request.httpBody = jsonData
        } catch {
            isLoading = false
            completion(.failure(error))
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let projectId = json["project_id"] as? String {
                        self?.fetchProjects(completion: nil)
                        completion(.success(projectId))
                    } else {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                } catch {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
    
    func getProject(projectId: String, completion: @escaping (Result<Project, Error>) -> Void) {
        isLoading = true
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)") else {
            isLoading = false
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        let task = URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let projectData = json["project"] as? [String: Any] {
                        let projectJson = try JSONSerialization.data(withJSONObject: projectData, options: [])
                        let decoder = JSONDecoder()
                        let project = try decoder.decode(Project.self, from: projectJson)
                        self?.currentProject = project
                        
                        // Also load characters
                        if let charactersData = projectData["characters"] as? [[String: Any]] {
                            let charactersJson = try JSONSerialization.data(withJSONObject: charactersData, options: [])
                            self?.characters = try decoder.decode([Character].self, from: charactersJson)
                        }
                        
                        // Also load files
                        if let filesData = projectData["files"] as? [[String: Any]] {
                            let filesJson = try JSONSerialization.data(withJSONObject: filesData, options: [])
                            self?.files = try decoder.decode([ProjectFile].self, from: filesJson)
                        }
                        
                        completion(.success(project))
                    } else {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                } catch {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
    
    func addCharacter(projectId: String, characterName: String, llmName: String, background: String = "", completion: @escaping (Result<String, Error>) -> Void) {
        isLoading = true
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)/characters") else {
            isLoading = false
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let json: [String: Any] = [
            "character_name": characterName,
            "llm_name": llmName,
            "background": background
        ]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            request.httpBody = jsonData
        } catch {
            isLoading = false
            completion(.failure(error))
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let characterId = json["character_id"] as? String {
                        // Refresh the characters list
                        if let projectId = self?.currentProject?.id {
                            self?.getProject(projectId: projectId) { _ in }
                        }
                        completion(.success(characterId))
                    } else {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                } catch {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
    
    func restoreSession(projectId: String, sessionId: String, completion: @escaping (Result<Bool, Error>) -> Void) {
        isLoading = true
        guard let url = URL(string: "\(baseURL)/sessions/\(projectId)/restore/\(sessionId)") else {
            isLoading = false
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let mode = json["conversation_mode"] as? String {
                        self?.currentConversationMode = mode
                        completion(.success(true))
                    } else {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                } catch {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
    
    func uploadFile(projectId: String, fileURL: URL, description: String = "", isReference: Bool = false, isOutput: Bool = false, completion: @escaping (Result<String, Error>) -> Void) {
        isLoading = true
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)/files") else {
            isLoading = false
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        // Create a boundary string for multipart form data
        let boundary = UUID().uuidString
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        
        // Add the file data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        
        do {
            let fileData = try Data(contentsOf: fileURL)
            body.append(fileData)
            body.append("\r\n".data(using: .utf8)!)
            
            // Add description
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"description\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(description)\r\n".data(using: .utf8)!)
            
            // Add isReference
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"is_reference\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(isReference)\r\n".data(using: .utf8)!)
            
            // Add isOutput
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"is_output\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(isOutput)\r\n".data(using: .utf8)!)
            
            // End the form
            body.append("--\(boundary)--\r\n".data(using: .utf8)!)
            
            request.httpBody = body
        } catch {
            isLoading = false
            completion(.failure(error))
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let fileId = json["file_id"] as? String {
                        // Refresh files list
                        if let projectId = self?.currentProject?.id {
                            self?.getProject(projectId: projectId) { _ in }
                        }
                        completion(.success(fileId))
                    } else {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                } catch {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
}
