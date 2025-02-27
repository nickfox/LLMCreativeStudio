import Foundation
import Combine

// Protocol for the project store, enabling easier testing
protocol ProjectStoreProtocol {
    var projects: [Project] { get }
    var currentProject: Project? { get }
    var characters: [CharacterModel] { get }
    var files: [ProjectFile] { get }
    var isLoading: Bool { get }
    
    var projectsPublisher: Published<[Project]>.Publisher { get }
    var currentProjectPublisher: Published<Project?>.Publisher { get }
    var charactersPublisher: Published<[CharacterModel]>.Publisher { get }
    var filesPublisher: Published<[ProjectFile]>.Publisher { get }
    var isLoadingPublisher: Published<Bool>.Publisher { get }
    
    func setLoading(_ loading: Bool)
    func updateProjects(_ projects: [Project])
    func updateCurrentProject(_ project: Project?)
    func updateCharacters(_ characters: [CharacterModel])
    func updateFiles(_ files: [ProjectFile])
}

// Main implementation of the project store
class ProjectStore: ProjectStoreProtocol, ObservableObject {
    @Published var projects: [Project] = []
    @Published var currentProject: Project? = nil
    @Published var characters: [CharacterModel] = []
    @Published var files: [ProjectFile] = []
    @Published var isLoading: Bool = false
    
    var projectsPublisher: Published<[Project]>.Publisher { $projects }
    var currentProjectPublisher: Published<Project?>.Publisher { $currentProject }
    var charactersPublisher: Published<[CharacterModel]>.Publisher { $characters }
    var filesPublisher: Published<[ProjectFile]>.Publisher { $files }
    var isLoadingPublisher: Published<Bool>.Publisher { $isLoading }
    
    func setLoading(_ loading: Bool) {
        DispatchQueue.main.async {
            self.isLoading = loading
        }
    }
    
    func updateProjects(_ projects: [Project]) {
        DispatchQueue.main.async {
            self.projects = projects
        }
    }
    
    func updateCurrentProject(_ project: Project?) {
        DispatchQueue.main.async {
            self.currentProject = project
        }
    }
    
    func updateCharacters(_ characters: [CharacterModel]) {
        DispatchQueue.main.async {
            self.characters = characters
        }
    }
    
    func updateFiles(_ files: [ProjectFile]) {
        DispatchQueue.main.async {
            self.files = files
        }
    }
}