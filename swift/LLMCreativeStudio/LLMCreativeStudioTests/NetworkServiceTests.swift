import XCTest
@testable import LLMCreativeStudio

class MockURLSession: URLSession {
    var data: Data?
    var response: URLResponse?
    var error: Error?
    
    func mockResponse(data: Data?, response: URLResponse?, error: Error?) {
        self.data = data
        self.response = response
        self.error = error
    }
    
    override func data(for request: URLRequest, delegate: URLSessionTaskDelegate? = nil) async throws -> (Data, URLResponse) {
        if let error = error {
            throw error
        }
        
        guard let data = data, let response = response else {
            throw NetworkError.noData
        }
        
        return (data, response)
    }
    
    override func data(from url: URL, delegate: URLSessionTaskDelegate? = nil) async throws -> (Data, URLResponse) {
        if let error = error {
            throw error
        }
        
        guard let data = data, let response = response else {
            throw NetworkError.noData
        }
        
        return (data, response)
    }
}

class NetworkServiceTests: XCTestCase {
    var networkService: NetworkService!
    var mockSession: MockURLSession!
    
    let testBaseURL = "http://test-server.com"
    
    override func setUp() {
        super.setUp()
        mockSession = MockURLSession()
        networkService = NetworkService(baseURL: testBaseURL, session: mockSession)
    }
    
    override func tearDown() {
        networkService = nil
        mockSession = nil
        super.tearDown()
    }
    
    // MARK: - Send Message Tests
    
    func testSendMessageSuccess() async throws {
        // Prepare mock response
        let responseJSON = """
        {
            "llm": "claude",
            "response": "This is a test response"
        }
        """
        let responseData = responseJSON.data(using: .utf8)!
        let response = HTTPURLResponse(url: URL(string: "\(testBaseURL)/chat")!, statusCode: 200, httpVersion: nil, headerFields: nil)
        
        mockSession.mockResponse(data: responseData, response: response, error: nil)
        
        // Call method
        let result = try await networkService.sendMessage(
            message: "Test message",
            llmName: "claude",
            dataQuery: "",
            sessionId: "test-session",
            currentConversationMode: "open",
            projectId: nil,
            recentContext: []
        )
        
        // Verify results
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result[0].llm, "claude")
        XCTAssertEqual(result[0].response, "This is a test response")
        XCTAssertEqual(result[0].content, "This is a test response")
    }
    
    func testSendMessageWithArrayResponse() async throws {
        // Prepare mock response
        let responseJSON = """
        [
            {
                "llm": "claude",
                "response": "Response from Claude"
            },
            {
                "llm": "chatgpt",
                "response": "Response from ChatGPT"
            }
        ]
        """
        let responseData = responseJSON.data(using: .utf8)!
        let response = HTTPURLResponse(url: URL(string: "\(testBaseURL)/chat")!, statusCode: 200, httpVersion: nil, headerFields: nil)
        
        mockSession.mockResponse(data: responseData, response: response, error: nil)
        
        // Call method
        let result = try await networkService.sendMessage(
            message: "Test message",
            llmName: "all",
            dataQuery: "",
            sessionId: "test-session",
            currentConversationMode: "open",
            projectId: nil,
            recentContext: []
        )
        
        // Verify results
        XCTAssertEqual(result.count, 2)
        XCTAssertEqual(result[0].llm, "claude")
        XCTAssertEqual(result[0].response, "Response from Claude")
        XCTAssertEqual(result[1].llm, "chatgpt")
        XCTAssertEqual(result[1].response, "Response from ChatGPT")
    }
    
    func testSendMessageWithDebateResponse() async throws {
        // Prepare mock response
        let responseJSON = """
        [
            {
                "content": "Opening statement from Claude.",
                "sender": "claude",
                "debate_round": 1,
                "debate_state": "opening_statements",
                "waiting_for_user": true,
                "action_required": "Please provide your opening statement."
            }
        ]
        """
        let responseData = responseJSON.data(using: .utf8)!
        let response = HTTPURLResponse(url: URL(string: "\(testBaseURL)/chat")!, statusCode: 200, httpVersion: nil, headerFields: nil)
        
        mockSession.mockResponse(data: responseData, response: response, error: nil)
        
        // Call method
        let result = try await networkService.sendMessage(
            message: "/debate topic",
            llmName: "all",
            dataQuery: "",
            sessionId: "test-session",
            currentConversationMode: "debate",
            projectId: nil,
            recentContext: []
        )
        
        // Verify results
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result[0].sender, "claude")
        XCTAssertEqual(result[0].content, "Opening statement from Claude.")
        XCTAssertEqual(result[0].debateRound, 1)
        XCTAssertEqual(result[0].debateState, "opening_statements")
        XCTAssertEqual(result[0].waitingForUser, true)
        XCTAssertEqual(result[0].actionRequired, "Please provide your opening statement.")
    }
    
    func testSendMessageWithError() async {
        // Prepare mock response
        let errorJSON = """
        {
            "error": "Invalid request format"
        }
        """
        let errorData = errorJSON.data(using: .utf8)!
        let response = HTTPURLResponse(url: URL(string: "\(testBaseURL)/chat")!, statusCode: 400, httpVersion: nil, headerFields: nil)
        
        mockSession.mockResponse(data: errorData, response: response, error: nil)
        
        // Call method and expect error
        do {
            _ = try await networkService.sendMessage(
                message: "Invalid message",
                llmName: "claude",
                dataQuery: "",
                sessionId: "test-session",
                currentConversationMode: "open",
                projectId: nil,
                recentContext: []
            )
            XCTFail("Expected an error to be thrown")
        } catch let error as NetworkError {
            // Verify error
            if case let .serverError(code, message) = error {
                XCTAssertEqual(code, 400)
                XCTAssertEqual(message, "Invalid request format")
            } else {
                XCTFail("Expected a serverError, got \(error)")
            }
        } catch {
            XCTFail("Expected a NetworkError, got \(error)")
        }
    }
    
    func testSendMessageWithNetworkFailure() async {
        // Prepare mock error
        let error = NSError(domain: "TestError", code: 1234, userInfo: [NSLocalizedDescriptionKey: "Network connection lost"])
        
        mockSession.mockResponse(data: nil, response: nil, error: error)
        
        // Call method and expect error
        do {
            _ = try await networkService.sendMessage(
                message: "Test message",
                llmName: "claude",
                dataQuery: "",
                sessionId: "test-session",
                currentConversationMode: "open",
                projectId: nil,
                recentContext: []
            )
            XCTFail("Expected an error to be thrown")
        } catch {
            // Just verify that an error was thrown - the actual error is handled by the system
            XCTAssertNotNil(error)
        }
    }
    
    // MARK: - Project Management Tests
    
    func testFetchProjectsSuccess() async throws {
        // Prepare mock response
        let responseJSON = """
        {
            "projects": [
                {
                    "id": "123",
                    "name": "Test Project",
                    "type": "creative",
                    "description": "A test project",
                    "created_at": "2023-01-01T12:00:00Z",
                    "updated_at": "2023-01-01T12:00:00Z"
                }
            ]
        }
        """
        let responseData = responseJSON.data(using: .utf8)!
        let response = HTTPURLResponse(url: URL(string: "\(testBaseURL)/projects")!, statusCode: 200, httpVersion: nil, headerFields: nil)
        
        mockSession.mockResponse(data: responseData, response: response, error: nil)
        
        // Call method
        let projects = try await networkService.fetchProjects()
        
        // Verify results
        XCTAssertEqual(projects.count, 1)
        XCTAssertEqual(projects[0].id, "123")
        XCTAssertEqual(projects[0].name, "Test Project")
        XCTAssertEqual(projects[0].type, "creative")
        XCTAssertEqual(projects[0].description, "A test project")
    }
    
    func testCreateProjectSuccess() async throws {
        // Prepare mock response
        let responseJSON = """
        {
            "project_id": "123"
        }
        """
        let responseData = responseJSON.data(using: .utf8)!
        let response = HTTPURLResponse(url: URL(string: "\(testBaseURL)/projects")!, statusCode: 201, httpVersion: nil, headerFields: nil)
        
        mockSession.mockResponse(data: responseData, response: response, error: nil)
        
        // Call method
        let projectId = try await networkService.createProject(
            name: "New Project",
            type: "creative",
            description: "A new test project"
        )
        
        // Verify results
        XCTAssertEqual(projectId, "123")
    }
    
    func testGetProjectSuccess() async throws {
        // Prepare mock response
        let responseJSON = """
        {
            "project": {
                "id": "123",
                "name": "Test Project",
                "type": "creative",
                "description": "A test project",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z",
                "characters": [
                    {
                        "id": "456",
                        "character_name": "John",
                        "llm_name": "claude",
                        "background": "A test character",
                        "created_at": "2023-01-01T12:00:00Z"
                    }
                ],
                "files": [
                    {
                        "id": "789",
                        "file_path": "/path/to/file.txt",
                        "file_type": "text",
                        "description": "A test file",
                        "is_reference": true,
                        "is_output": false,
                        "created_at": "2023-01-01T12:00:00Z"
                    }
                ]
            }
        }
        """
        let responseData = responseJSON.data(using: .utf8)!
        let response = HTTPURLResponse(url: URL(string: "\(testBaseURL)/projects/123")!, statusCode: 200, httpVersion: nil, headerFields: nil)
        
        mockSession.mockResponse(data: responseData, response: response, error: nil)
        
        // Call method
        let (project, characters, files) = try await networkService.getProject(projectId: "123")
        
        // Verify project
        XCTAssertEqual(project.id, "123")
        XCTAssertEqual(project.name, "Test Project")
        XCTAssertEqual(project.type, "creative")
        
        // Verify characters
        XCTAssertEqual(characters.count, 1)
        XCTAssertEqual(characters[0].id, "456")
        XCTAssertEqual(characters[0].character_name, "John")
        XCTAssertEqual(characters[0].llm_name, "claude")
        
        // Verify files
        XCTAssertEqual(files.count, 1)
        XCTAssertEqual(files[0].id, "789")
        XCTAssertEqual(files[0].file_path, "/path/to/file.txt")
        XCTAssertEqual(files[0].is_reference, true)
        XCTAssertEqual(files[0].is_output, false)
    }
}