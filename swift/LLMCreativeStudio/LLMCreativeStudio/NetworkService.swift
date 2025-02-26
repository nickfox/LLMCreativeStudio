import Foundation
import Combine

// API error types for better error handling
enum NetworkError: Error {
    case invalidURL
    case requestFailed(Error)
    case invalidResponse
    case decodingError(Error)
    case serverError(Int, String)
    case noData
    
    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .requestFailed(let error):
            return "Request failed: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid response from server"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .serverError(let code, let message):
            return "Server error (\(code)): \(message)"
        case .noData:
            return "No data received"
        }
    }
}

// Protocol for API service - enables easier mocking and testing
protocol APIServiceProtocol {
    func sendMessage(message: String, llmName: String, dataQuery: String, sessionId: String, currentConversationMode: String, projectId: String?, recentContext: [[String: Any]]) async throws -> [MessageResponse]
    func fetchProjects() async throws -> [Project]
    func createProject(name: String, type: String, description: String) async throws -> String
    func getProject(projectId: String) async throws -> (Project, [Character], [ProjectFile])
    func addCharacter(projectId: String, characterName: String, llmName: String, background: String) async throws -> String
    func restoreSession(projectId: String, sessionId: String) async throws -> String
    func uploadFile(projectId: String, fileURL: URL, description: String, isReference: Bool, isOutput: Bool) async throws -> String
}

// The main network service implementing the API protocol
class NetworkService: APIServiceProtocol {
    private let baseURL: String
    private var session: URLSession
    
    init(baseURL: String = "http://localhost:8000", session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }
    
    // MARK: - Message Handling
    
    func sendMessage(message: String, llmName: String, dataQuery: String = "", sessionId: String, currentConversationMode: String, projectId: String? = nil, recentContext: [[String: Any]]) async throws -> [MessageResponse] {
        guard let url = URL(string: "\(baseURL)/chat") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        var json: [String: Any] = [
            "llm_name": llmName,
            "message": message,
            "data_query": dataQuery,
            "session_id": sessionId,
            "conversation_mode": currentConversationMode,
            "context": recentContext
        ]
        
        // Add project ID if one is selected
        if let projectId = projectId {
            json["project_id"] = projectId
        }
        
        let jsonData = try JSONSerialization.data(withJSONObject: json)
        request.httpBody = jsonData
        
        // Log the request for debugging
        if let jsonString = String(data: jsonData, encoding: .utf8) {
            print("Sending JSON payload: \(jsonString)")
        }
        
        let (data, response) = try await session.data(for: request)
        
        // Log the raw response
        print("Received raw response from server:")
        print(String(data: data, encoding: .utf8) ?? "Could not decode response")
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        // Check for successful status code
        if !(200...299).contains(httpResponse.statusCode) {
            var errorMessage = "Unknown error"
            if let errorData = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let message = errorData["error"] as? String {
                errorMessage = message
            } else if let message = String(data: data, encoding: .utf8) {
                errorMessage = message
            }
            throw NetworkError.serverError(httpResponse.statusCode, errorMessage)
        }
        
        // Parse response based on format
        if let responseDict = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
           let responseText = responseDict["response"] as? String,
           let llmName = responseDict["llm"] as? String {
            // Single response
            let response = MessageResponse(
                llm: llmName,
                response: responseText,
                content: responseText,
                sender: llmName,
                debateRound: nil,
                debateState: nil,
                waitingForUser: nil,
                actionRequired: nil
            )
            return [response]
        } else if let responseArray = try? JSONSerialization.jsonObject(with: data, options: []) as? [[String: Any]] {
            // Array of responses - handle both old and new formats
            return responseArray.compactMap { responseDict in
                if let responseText = responseDict["response"] as? String,
                   let llmName = responseDict["llm"] as? String {
                    // Old format
                    return MessageResponse(
                        llm: llmName,
                        response: responseText,
                        content: responseText,
                        sender: llmName,
                        debateRound: nil,
                        debateState: nil,
                        waitingForUser: nil,
                        actionRequired: nil
                    )
                } else if let contentText = responseDict["content"] as? String,
                          let sender = responseDict["sender"] as? String {
                    // New debate format
                    let debateRound = responseDict["debate_round"] as? Int
                    let debateState = responseDict["debate_state"] as? String
                    let waitingForUser = responseDict["waiting_for_user"] as? Bool
                    let actionRequired = responseDict["action_required"] as? String
                    
                    return MessageResponse(
                        llm: sender,  // Using sender as llm for debate format
                        response: contentText,
                        content: contentText,
                        sender: sender,
                        debateRound: debateRound,
                        debateState: debateState,
                        waitingForUser: waitingForUser,
                        actionRequired: actionRequired
                    )
                }
                return nil
            }
        }
        
        throw NetworkError.decodingError(NSError(domain: "Invalid response format", code: 0, userInfo: nil))
    }
    
    // MARK: - Project Management
    
    func fetchProjects() async throws -> [Project] {
        guard let url = URL(string: "\(baseURL)/projects") else {
            throw NetworkError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
        
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let projectsData = json["projects"] as? [[String: Any]] else {
            throw NetworkError.decodingError(NSError(domain: "Invalid response format", code: 0, userInfo: nil))
        }
        
        let decoder = JSONDecoder()
        let projectsJsonData = try JSONSerialization.data(withJSONObject: projectsData)
        let projects = try decoder.decode([Project].self, from: projectsJsonData)
        
        return projects
    }
    
    func createProject(name: String, type: String, description: String) async throws -> String {
        guard let url = URL(string: "\(baseURL)/projects") else {
            throw NetworkError.invalidURL
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
        
        let jsonData = try JSONSerialization.data(withJSONObject: json)
        request.httpBody = jsonData
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
        
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let projectId = json["project_id"] as? String else {
            throw NetworkError.decodingError(NSError(domain: "Invalid response format", code: 0, userInfo: nil))
        }
        
        return projectId
    }
    
    func getProject(projectId: String) async throws -> (Project, [Character], [ProjectFile]) {
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)") else {
            throw NetworkError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
        
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let projectData = json["project"] as? [String: Any] else {
            throw NetworkError.decodingError(NSError(domain: "Invalid response format", code: 0, userInfo: nil))
        }
        
        let decoder = JSONDecoder()
        
        // Decode project
        let projectJson = try JSONSerialization.data(withJSONObject: projectData)
        let project = try decoder.decode(Project.self, from: projectJson)
        
        // Decode characters if available
        var characters: [Character] = []
        if let charactersData = projectData["characters"] as? [[String: Any]] {
            let charactersJson = try JSONSerialization.data(withJSONObject: charactersData)
            characters = try decoder.decode([Character].self, from: charactersJson)
        }
        
        // Decode files if available
        var files: [ProjectFile] = []
        if let filesData = projectData["files"] as? [[String: Any]] {
            let filesJson = try JSONSerialization.data(withJSONObject: filesData)
            files = try decoder.decode([ProjectFile].self, from: filesJson)
        }
        
        return (project, characters, files)
    }
    
    func addCharacter(projectId: String, characterName: String, llmName: String, background: String = "") async throws -> String {
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)/characters") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let json: [String: Any] = [
            "character_name": characterName,
            "llm_name": llmName,
            "background": background
        ]
        
        let jsonData = try JSONSerialization.data(withJSONObject: json)
        request.httpBody = jsonData
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
        
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let characterId = json["character_id"] as? String else {
            throw NetworkError.decodingError(NSError(domain: "Invalid response format", code: 0, userInfo: nil))
        }
        
        return characterId
    }
    
    func restoreSession(projectId: String, sessionId: String) async throws -> String {
        guard let url = URL(string: "\(baseURL)/sessions/\(projectId)/restore/\(sessionId)") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
        
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let mode = json["conversation_mode"] as? String else {
            throw NetworkError.decodingError(NSError(domain: "Invalid response format", code: 0, userInfo: nil))
        }
        
        return mode
    }
    
    func uploadFile(projectId: String, fileURL: URL, description: String = "", isReference: Bool = false, isOutput: Bool = false) async throws -> String {
        guard let url = URL(string: "\(baseURL)/projects/\(projectId)/files") else {
            throw NetworkError.invalidURL
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
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
        
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let fileId = json["file_id"] as? String else {
            throw NetworkError.decodingError(NSError(domain: "Invalid response format", code: 0, userInfo: nil))
        }
        
        return fileId
    }
}

// MARK: - Response Models

struct MessageResponse: Codable {
    let llm: String
    let response: String
    let content: String
    let sender: String
    let debateRound: Int?
    let debateState: String?
    let waitingForUser: Bool?
    let actionRequired: String?
}

// Data helpers
extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}