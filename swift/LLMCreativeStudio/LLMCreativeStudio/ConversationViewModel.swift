import Foundation
import Combine

// The main view model that coordinates interactions between views and the data layer
class ConversationViewModel: ObservableObject {
    // State
    @Published var currentConversationMode: String = "open"
    @Published var sessionId: String = UUID().uuidString
    @Published var isLoading: Bool = false
    
    // Dependencies
    private let networkService: APIServiceProtocol
    private let messageStore: MessageStoreProtocol
    private let projectStore: ProjectStoreProtocol
    
    // Cancellables
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Computed Properties
    
    var messages: [Message] {
        messageStore.messages
    }
    
    var projects: [Project] {
        projectStore.projects
    }
    
    var currentProject: Project? {
        projectStore.currentProject
    }
    
    var characters: [Character] {
        projectStore.characters
    }
    
    var files: [ProjectFile] {
        projectStore.files
    }
    
    // MARK: - Initialization
    
    init(networkService: APIServiceProtocol = NetworkService(),
         messageStore: MessageStoreProtocol = MessageStore(),
         projectStore: ProjectStoreProtocol = ProjectStore()) {
        self.networkService = networkService
        self.messageStore = messageStore
        self.projectStore = projectStore
        
        // Set up bindings
        setupBindings()
    }
    
    private func setupBindings() {
        // Here we can set up any reactive bindings between our dependencies
        projectStore.isLoadingPublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] loading in
                self?.isLoading = loading
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Message Handling
    
    func sendMessage(text: String) async {
        guard !text.isEmpty else { return }
        
        // Parse the message to determine LLM target
        let (llmName, parsedMessage, dataQuery) = messageStore.parseMessage(text, characters: characters)
        
        // Add user message to the store
        messageStore.addMessage(
            text: text,
            sender: "user",
            senderName: "You",
            referencedMessageId: nil,
            messageIntent: nil
        )
        
        do {
            // Set loading state
            projectStore.setLoading(true)
            
            // Get recent context for the API call
            let recentContext = messageStore.getRecentContext()
            
            // Send message to the server
            let responses = try await networkService.sendMessage(
                message: parsedMessage,
                llmName: llmName,
                dataQuery: dataQuery,
                sessionId: sessionId,
                currentConversationMode: currentConversationMode,
                projectId: currentProject?.id,
                recentContext: recentContext
            )
            
            // Process responses
            for response in responses {
                let senderName = messageStore.getSenderName(for: response.sender, characters: characters)
                
                messageStore.addMessage(
                    text: response.content,
                    sender: response.sender,
                    senderName: senderName,
                    referencedMessageId: nil,
                    messageIntent: nil
                )
            }
        } catch let error as NetworkError {
            handleNetworkError(error)
        } catch {
            // Handle other errors
            messageStore.addMessage(
                text: "Error: \(error.localizedDescription)",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
        }
        
        // Reset loading state
        projectStore.setLoading(false)
    }
    
    func clearMessages() {
        messageStore.clearMessages()
    }
    
    // MARK: - Project Management
    
    func fetchProjects() async {
        do {
            projectStore.setLoading(true)
            let projects = try await networkService.fetchProjects()
            projectStore.updateProjects(projects)
        } catch let error as NetworkError {
            handleNetworkError(error)
        } catch {
            messageStore.addMessage(
                text: "Error fetching projects: \(error.localizedDescription)",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
        }
        projectStore.setLoading(false)
    }
    
    func createProject(name: String, type: String, description: String) async -> Bool {
        do {
            projectStore.setLoading(true)
            let projectId = try await networkService.createProject(name: name, type: type, description: description)
            
            // Refresh projects list
            await fetchProjects()
            
            return true
        } catch let error as NetworkError {
            handleNetworkError(error)
            return false
        } catch {
            messageStore.addMessage(
                text: "Error creating project: \(error.localizedDescription)",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
            projectStore.setLoading(false)
            return false
        }
    }
    
    func loadProject(projectId: String) async {
        do {
            projectStore.setLoading(true)
            
            let (project, characters, files) = try await networkService.getProject(projectId: projectId)
            
            projectStore.updateCurrentProject(project)
            projectStore.updateCharacters(characters)
            projectStore.updateFiles(files)
            
            // Generate a new session ID for the new project
            sessionId = UUID().uuidString
            
            // Clear existing messages
            clearMessages()
            
        } catch let error as NetworkError {
            handleNetworkError(error)
        } catch {
            messageStore.addMessage(
                text: "Error loading project: \(error.localizedDescription)",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
        }
        
        projectStore.setLoading(false)
    }
    
    func addCharacter(characterName: String, llmName: String, background: String = "") async -> Bool {
        guard let projectId = currentProject?.id else {
            messageStore.addMessage(
                text: "Error: No project selected",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
            return false
        }
        
        do {
            projectStore.setLoading(true)
            let _ = try await networkService.addCharacter(
                projectId: projectId,
                characterName: characterName,
                llmName: llmName,
                background: background
            )
            
            // Refresh project to update characters
            await loadProject(projectId: projectId)
            
            return true
        } catch let error as NetworkError {
            handleNetworkError(error)
            return false
        } catch {
            messageStore.addMessage(
                text: "Error adding character: \(error.localizedDescription)",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
            projectStore.setLoading(false)
            return false
        }
    }
    
    func uploadFile(fileURL: URL, description: String = "", isReference: Bool = false, isOutput: Bool = false) async -> Bool {
        guard let projectId = currentProject?.id else {
            messageStore.addMessage(
                text: "Error: No project selected",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
            return false
        }
        
        do {
            projectStore.setLoading(true)
            let _ = try await networkService.uploadFile(
                projectId: projectId,
                fileURL: fileURL,
                description: description,
                isReference: isReference,
                isOutput: isOutput
            )
            
            // Refresh project to update files
            await loadProject(projectId: projectId)
            
            return true
        } catch let error as NetworkError {
            handleNetworkError(error)
            return false
        } catch {
            messageStore.addMessage(
                text: "Error uploading file: \(error.localizedDescription)",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
            projectStore.setLoading(false)
            return false
        }
    }
    
    func restoreSession(projectId: String, sessionId: String) async -> Bool {
        do {
            projectStore.setLoading(true)
            let mode = try await networkService.restoreSession(projectId: projectId, sessionId: sessionId)
            
            self.currentConversationMode = mode
            self.sessionId = sessionId
            
            projectStore.setLoading(false)
            return true
        } catch let error as NetworkError {
            handleNetworkError(error)
            return false
        } catch {
            messageStore.addMessage(
                text: "Error restoring session: \(error.localizedDescription)",
                sender: "system",
                senderName: "System",
                referencedMessageId: nil,
                messageIntent: "error"
            )
            projectStore.setLoading(false)
            return false
        }
    }
    
    // MARK: - Error Handling
    
    private func handleNetworkError(_ error: NetworkError) {
        var errorMessage = "Network error: "
        
        switch error {
        case .invalidURL:
            errorMessage += "Invalid URL"
        case .requestFailed(let underlyingError):
            errorMessage += "Request failed - \(underlyingError.localizedDescription)"
        case .invalidResponse:
            errorMessage += "Invalid response from server"
        case .decodingError(let underlyingError):
            errorMessage += "Failed to decode response - \(underlyingError.localizedDescription)"
        case .serverError(let code, let message):
            errorMessage += "Server error (\(code)): \(message)"
        case .noData:
            errorMessage += "No data received"
        }
        
        messageStore.addMessage(
            text: errorMessage,
            sender: "system",
            senderName: "System",
            referencedMessageId: nil,
            messageIntent: "error"
        )
        
        projectStore.setLoading(false)
    }
}