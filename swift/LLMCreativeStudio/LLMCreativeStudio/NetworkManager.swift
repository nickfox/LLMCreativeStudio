// NetworkManager.swift

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

struct CharacterModel: Identifiable, Codable {
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

struct RAGSource: Identifiable, Codable {
    let id = UUID()
    let document_id: String
    let chunk_id: Int
    let similarity: Double
    let text_preview: String
    
    enum CodingKeys: String, CodingKey {
        case document_id, chunk_id, similarity, text_preview
    }
}

struct RAGMetadata: Codable {
    let retrieval_time_ms: Int
    let generation_time_ms: Int
    let total_time_ms: Int
    
    enum CodingKeys: String, CodingKey {
        case retrieval_time_ms, generation_time_ms, total_time_ms
    }
}

struct ProcessingResults {
    let total: Int
    let processed: Int
    let failed: Int
    let details: [[String: Any]]
}

class NetworkManager: ObservableObject {
    @Published var messages: [Message] = []
    @Published var currentConversationMode: String = "open"
    @Published var projects: [Project] = []
    @Published var currentProject: Project?
    @Published var characters: [CharacterModel] = []
    @Published var files: [ProjectFile] = []
    @Published var isLoading: Bool = false
    
    let baseURL = "http://localhost:8000"
    var sessionId = UUID().uuidString
    
    // MARK: - Chat Methods
    
    func addMessage(text: String, sender: String, senderName: String) {
        let message = Message(
            text: text,
            sender: sender,
            senderName: senderName
        )
        DispatchQueue.main.async {
            self.messages.append(message)
        }
    }
    
    func clearMessages() {
        DispatchQueue.main.async {
            self.messages.removeAll()
        }
    }
    
    func parseMessage(_ message: String) -> (llmName: String, message: String, dataQuery: String) {
        // Default values
        var llmName = "all"  // Changed from "claude" to "all" to route to all LLMs by default
        var parsedMessage = message
        var dataQuery = ""
        
        // Check for RAG query
        if message.hasPrefix("?") {
            return ("rag", message, "")
        }
        
        // Check for @mentions
        let mentionPrefixes = ["@claude", "@chatgpt", "@gemini", "@all"]
        for prefix in mentionPrefixes {
            if message.lowercased().hasPrefix(prefix.lowercased()) {
                // Extract LLM name without the @
                llmName = String(prefix.dropFirst())
                
                // Remove the prefix from the message
                parsedMessage = message.dropFirst(prefix.count).trimmingCharacters(in: .whitespacesAndNewlines)
                
                break
            }
        }
        
        // Check for data query (:: separator)
        if parsedMessage.contains("::") {
            let components = parsedMessage.components(separatedBy: "::")
            if components.count >= 2 {
                parsedMessage = components[0].trimmingCharacters(in: .whitespacesAndNewlines)
                dataQuery = components[1].trimmingCharacters(in: .whitespacesAndNewlines)
            }
        }
        
        return (llmName, parsedMessage, dataQuery)
    }
    
    func sendMessage(message: String, llmName: String, dataQuery: String, sessionId: String) {
        // If RAG query, handle differently
        if llmName == "rag" {
            sendRAGQuery(query: message) { [weak self] result in
                switch result {
                case .success(let ragMessage):
                    DispatchQueue.main.async {
                        self?.messages.append(ragMessage)
                    }
                case .failure(let error):
                    print("RAG query error: \(error)")
                    DispatchQueue.main.async {
                        self?.addMessage(
                            text: "Error processing RAG query: \(error.localizedDescription)",
                            sender: "system",
                            senderName: "System"
                        )
                    }
                }
            }
            return
        }
        
        guard let url = URL(string: "\(baseURL)/chat") else {
            print("Invalid URL")
            return
        }
        
        let json: [String: Any] = [
            "llm_name": llmName,
            "message": message,
            "data_query": dataQuery,
            "session_id": sessionId,
            "project_id": currentProject?.id as Any,
            "conversation_mode": currentConversationMode
        ]
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json)
            request.httpBody = jsonData
            
            let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
                if let error = error {
                    print("Error sending message: \(error)")
                    DispatchQueue.main.async {
                        self?.addMessage(
                            text: "Error: \(error.localizedDescription)",
                            sender: "system",
                            senderName: "System"
                        )
                    }
                    return
                }
                
                guard let data = data else {
                    print("No data received")
                    return
                }
                
                do {
                    if let responsesArray = try JSONSerialization.jsonObject(with: data, options: []) as? [[String: Any]] {
                        
                        for responseDict in responsesArray {
                            var text = ""
                            var sender = "system"
                            var senderName = "System"
                            let referencedMessageId: UUID? = nil
                            let conversationMode: String? = nil
                            let messageIntent: String? = nil
                            var debateRound: Int? = nil
                            var debateState: String? = nil
                            var waitingForUser: Bool? = nil
                            var actionRequired: String? = nil
                            
                            // Handle both response formats
                            if let content = responseDict["content"] as? String {
                                text = content
                                sender = responseDict["sender"] as? String ?? "system"
                                
                                // Determine sender name from sender
                                switch sender.lowercased() {
                                case "claude": senderName = "Claude"
                                case "chatgpt": senderName = "ChatGPT"
                                case "gemini": senderName = "Gemini"
                                case "system": senderName = "System"
                                case "research_assistant": senderName = "Research Assistant"
                                default: senderName = sender.capitalized
                                }
                                
                                // Check for debate properties
                                if let round = responseDict["debate_round"] as? Int {
                                    debateRound = round
                                }
                                
                                if let state = responseDict["debate_state"] as? String {
                                    debateState = state
                                }
                                
                                if let waiting = responseDict["waiting_for_user"] as? Bool {
                                    waitingForUser = waiting
                                }
                                
                                if let action = responseDict["action_required"] as? String {
                                    actionRequired = action
                                }
                                
                            } else if let response = responseDict["response"] as? String {
                                text = response
                                
                                if let llm = responseDict["llm"] as? String {
                                    sender = llm
                                    
                                    // Determine sender name from LLM
                                    switch llm.lowercased() {
                                    case "claude": senderName = "Claude"
                                    case "chatgpt": senderName = "ChatGPT"
                                    case "gemini": senderName = "Gemini"
                                    case "system": senderName = "System"
                                    default: senderName = llm.capitalized
                                    }
                                }
                            }
                            
                            // Create and add the message
                            DispatchQueue.main.async {
                                let message = Message(
                                    text: text,
                                    sender: sender,
                                    senderName: senderName,
                                    referencedMessageId: referencedMessageId,
                                    conversationMode: conversationMode,
                                    messageIntent: messageIntent,
                                    debateRound: debateRound,
                                    debateState: debateState,
                                    waitingForUser: waitingForUser,
                                    actionRequired: actionRequired
                                )
                                self?.messages.append(message)
                            }
                        }
                    }
                } catch {
                    print("Error parsing response: \(error)")
                    DispatchQueue.main.async {
                        self?.addMessage(
                            text: "Error parsing response: \(error.localizedDescription)",
                            sender: "system",
                            senderName: "System"
                        )
                    }
                }
            }
            task.resume()
            
        } catch {
            print("Error encoding JSON: \(error)")
            addMessage(
                text: "Error sending message: \(error.localizedDescription)",
                sender: "system",
                senderName: "System"
            )
        }
    }
    
    // MARK: - RAG Methods
    
    func processDocumentForRAG(projectId: String, documentId: String, completion: @escaping (Result<Bool, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)/documents/\(documentId)/process") else {
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                }
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                   let _ = json["message"] as? String {
                    DispatchQueue.main.async {
                        completion(.success(true))
                    }
                } else {
                    DispatchQueue.main.async {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
    
    func processAllDocumentsForRAG(projectId: String, completion: @escaping (Result<ProcessingResults, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)/process_all_documents") else {
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                }
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                   let total = json["total_documents"] as? Int,
                   let processed = json["processed"] as? Int,
                   let failed = json["failed"] as? Int {
                    
                    let details = json["details"] as? [[String: Any]] ?? []
                    
                    let results = ProcessingResults(
                        total: total,
                        processed: processed,
                        failed: failed,
                        details: details
                    )
                    
                    DispatchQueue.main.async {
                        completion(.success(results))
                    }
                } else {
                    DispatchQueue.main.async {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
    
    func sendRAGQuery(query: String, completion: @escaping (Result<Message, Error>) -> Void) {
        guard let projectId = currentProject?.id else {
            completion(.failure(NSError(domain: "No project selected", code: 0, userInfo: nil)))
            return
        }
        
        guard let url = URL(string: "\(baseURL)/rag/query") else {
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        // Remove ? prefix if present
        let cleanQuery = query.hasPrefix("?") ? String(query.dropFirst()).trimmingCharacters(in: .whitespacesAndNewlines) : query
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let json: [String: Any] = [
            "query": cleanQuery,
            "project_id": projectId,
            "use_thinking": false
        ]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            request.httpBody = jsonData
        } catch {
            completion(.failure(error))
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                }
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                   let answer = json["answer"] as? String {
                    
                    // Get sources if available
                    var sourcesText = ""
                    if let sources = json["sources"] as? [[String: Any]], !sources.isEmpty {
                        sourcesText = "\n\nSources:\n"
                        for (index, source) in sources.enumerated() {
                            if let docId = source["document_id"] as? String,
                               let preview = source["text_preview"] as? String,
                               let similarity = source["similarity"] as? Double {
                                sourcesText += "\(index + 1). Document \(docId) (Relevance: \(String(format: "%.0f%%", similarity * 100))):\n\(preview)\n\n"
                            }
                        }
                    }
                    
                    // Create a message with the RAG response
                    let message = Message(
                        text: answer + sourcesText,
                        sender: "research_assistant",
                        senderName: "Research Assistant",
                        timestamp: Date()
                    )
                    
                    DispatchQueue.main.async {
                        completion(.success(message))
                    }
                } else {
                    DispatchQueue.main.async {
                        completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
        task.resume()
    }
    
    // MARK: - File Management Methods
    
    func uploadFile(projectId: String, fileURL: URL, description: String, isReference: Bool, completion: @escaping (Result<String, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)/files") else {
            completion(.failure(NSError(domain: "Invalid URL", code: 0, userInfo: nil)))
            return
        }
        
        // Create a boundary for multipart form data
        let boundary = UUID().uuidString
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        // Create the form data
        do {
            let fileData = try Data(contentsOf: fileURL)
            let filename = fileURL.lastPathComponent
            let mimeType = mimeTypeForPath(path: fileURL.path)
            
            var formData = Data()
            
            // Add file part
            formData.append("--\(boundary)\r\n".data(using: .utf8)!)
            formData.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
            formData.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
            formData.append(fileData)
            formData.append("\r\n".data(using: .utf8)!)
            
            // Add description part
            formData.append("--\(boundary)\r\n".data(using: .utf8)!)
            formData.append("Content-Disposition: form-data; name=\"description\"\r\n\r\n".data(using: .utf8)!)
            formData.append("\(description)\r\n".data(using: .utf8)!)
            
            // Add is_reference part
            formData.append("--\(boundary)\r\n".data(using: .utf8)!)
            formData.append("Content-Disposition: form-data; name=\"is_reference\"\r\n\r\n".data(using: .utf8)!)
            formData.append("\(isReference)\r\n".data(using: .utf8)!)
            
            // Add is_output part
            formData.append("--\(boundary)\r\n".data(using: .utf8)!)
            formData.append("Content-Disposition: form-data; name=\"is_output\"\r\n\r\n".data(using: .utf8)!)
            formData.append("\(!isReference)\r\n".data(using: .utf8)!)
            
            // Add closing boundary
            formData.append("--\(boundary)--\r\n".data(using: .utf8)!)
            
            request.httpBody = formData
            
            let task = URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    DispatchQueue.main.async {
                        completion(.failure(error))
                    }
                    return
                }
                
                guard let data = data else {
                    DispatchQueue.main.async {
                        completion(.failure(NSError(domain: "No data received", code: 0, userInfo: nil)))
                    }
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let fileId = json["file_id"] as? String {
                        DispatchQueue.main.async {
                            completion(.success(fileId))
                        }
                    } else {
                        DispatchQueue.main.async {
                            completion(.failure(NSError(domain: "Invalid response format", code: 0, userInfo: nil)))
                        }
                    }
                } catch {
                    DispatchQueue.main.async {
                        completion(.failure(error))
                    }
                }
            }
            
            task.resume()
            
        } catch {
            completion(.failure(error))
        }
    }
    
    func downloadFile(projectId: String, fileId: String, completion: @escaping (Result<URL, Error>) -> Void) {
        let downloadURL = URL(string: "\(baseURL)/projects/\(projectId)/files/\(fileId)/download")!
        
        let task = URLSession.shared.downloadTask(with: downloadURL) { tempURL, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
                return
            }
            
            guard let tempURL = tempURL else {
                DispatchQueue.main.async {
                    completion(.failure(NSError(domain: "No file downloaded", code: 0, userInfo: nil)))
                }
                return
            }
            
            // Get the suggested filename from the response headers
            var filename = "downloaded_file"
            if let disposition = (response as? HTTPURLResponse)?.allHeaderFields["Content-Disposition"] as? String {
                let filenameRange = disposition.range(of: "filename=")
                if let range = filenameRange {
                    let filenameWithQuotes = disposition[range.upperBound...]
                    filename = filenameWithQuotes.replacingOccurrences(of: "\"", with: "")
                    if filename.contains(";") {
                        filename = filename.components(separatedBy: ";").first ?? filename
                    }
                }
            }
            
            // Create a unique path in the Downloads directory
            let downloadsURL = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask).first!
            let destinationURL = downloadsURL.appendingPathComponent(filename)
            
            // Remove any existing file
            try? FileManager.default.removeItem(at: destinationURL)
            
            do {
                // Move the file to the destination
                try FileManager.default.moveItem(at: tempURL, to: destinationURL)
                
                DispatchQueue.main.async {
                    completion(.success(destinationURL))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
        
        task.resume()
    }
    
    func loadProjectFiles(projectId: String) {
        let url = URL(string: "\(baseURL)/projects/\(projectId)/files")!
        
        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            guard let self = self else { return }
            
            guard error == nil, let data = data else {
                print("Error loading files: \(error?.localizedDescription ?? "Unknown error")")
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                   let filesData = json["files"] as? [[String: Any]] {
                    let filesJson = try JSONSerialization.data(withJSONObject: filesData, options: [])
                    let files = try JSONDecoder().decode([ProjectFile].self, from: filesJson)
                    
                    DispatchQueue.main.async {
                        self.files = files
                    }
                }
            } catch {
                print("Error parsing files: \(error)")
            }
        }.resume()
    }
    
    // MARK: - Helper Methods
    
    private func mimeTypeForPath(path: String) -> String {
        let url = URL(fileURLWithPath: path)
        let pathExtension = url.pathExtension
        
        switch pathExtension.lowercased() {
        case "pdf":
            return "application/pdf"
        case "txt":
            return "text/plain"
        case "md":
            return "text/markdown"
        case "docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        case "csv":
            return "text/csv"
        case "xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        case "jpg", "jpeg":
            return "image/jpeg"
        case "png":
            return "image/png"
        default:
            return "application/octet-stream"
        }
    }
}