// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudioTests/ProjectViewTests.swift

import XCTest
import SwiftUI
@testable import LLMCreativeStudio

final class ProjectViewTests: XCTestCase {
    
    var networkManager: NetworkManager!
    
    override func setUp() {
        super.setUp()
        networkManager = NetworkManager()
    }
    
    override func tearDown() {
        networkManager = nil
        super.tearDown()
    }
    
    // Basic model tests that don't require ViewInspector
    
    func testProjectModel() {
        // Create a test project
        let project = Project(
            id: "1",
            name: "Test Project",
            type: "research",
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        
        // Verify the project properties
        XCTAssertEqual(project.id, "1")
        XCTAssertEqual(project.name, "Test Project")
        XCTAssertEqual(project.type, "research")
        XCTAssertEqual(project.description, "Test description")
        XCTAssertEqual(project.created_at, "2023-01-01T00:00:00Z")
        XCTAssertEqual(project.updated_at, "2023-01-01T00:00:00Z")
    }
    
    func testNetworkManagerProjectState() {
        // Add some test projects
        let project1 = Project(
            id: "1",
            name: "Test Project 1",
            type: "research", 
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        
        let project2 = Project(
            id: "2",
            name: "Test Project 2",
            type: "songwriting",
            description: "Another test description",
            created_at: "2023-01-02T00:00:00Z",
            updated_at: "2023-01-02T00:00:00Z"
        )
        
        networkManager.projects = [project1, project2]
        
        // Test that projects were stored correctly
        XCTAssertEqual(networkManager.projects.count, 2)
        XCTAssertEqual(networkManager.projects[0].name, "Test Project 1")
        XCTAssertEqual(networkManager.projects[1].name, "Test Project 2")
    }
    
    func testCurrentProject() {
        // Create a test project
        let project = Project(
            id: "1",
            name: "Test Project",
            type: "research",
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        
        // Set the current project
        networkManager.currentProject = project
        
        // Test that the current project was set correctly
        XCTAssertNotNil(networkManager.currentProject)
        XCTAssertEqual(networkManager.currentProject?.id, "1")
        XCTAssertEqual(networkManager.currentProject?.name, "Test Project")
    }
    
    // Note: The UI tests have been commented out as they require ViewInspector
    // To enable them, add ViewInspector to the project via Swift Package Manager
    
    /*
    func testProjectViewWithNoProjects() throws {
        // Create the view with empty projects list
        let view = ProjectView()
            .environmentObject(networkManager)
        
        // This requires ViewInspector to test the UI
    }
    
    func testProjectViewWithProjects() throws {
        // Add some test projects
        let project1 = Project(
            id: "1",
            name: "Test Project 1",
            type: "research", 
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        
        let project2 = Project(
            id: "2",
            name: "Test Project 2",
            type: "songwriting",
            description: "Another test description",
            created_at: "2023-01-02T00:00:00Z",
            updated_at: "2023-01-02T00:00:00Z"
        )
        
        networkManager.projects = [project1, project2]
        
        // Create the view
        let view = ProjectView()
            .environmentObject(networkManager)
        
        // This requires ViewInspector to test the UI
    }
    
    func testCreateProjectView() throws {
        let view = CreateProjectView()
            .environmentObject(networkManager)
        
        // This requires ViewInspector to test the UI
    }
    
    func testProjectRow() throws {
        // Create a test project
        let project = Project(
            id: "1",
            name: "Test Project",
            type: "research",
            description: "Test description",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z"
        )
        
        // Create the view
        let view = ProjectRow(project: project)
            .environmentObject(networkManager)
        
        // This requires ViewInspector to test the UI
    }
    */
}
