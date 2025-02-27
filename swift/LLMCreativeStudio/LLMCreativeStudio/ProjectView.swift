// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/ProjectView.swift

import SwiftUI
import AppKit

struct ProjectView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var isShowingCreateProject = false
    
    var body: some View {
        VStack {
            HStack {
                Text("Projects")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .frame(maxWidth: .infinity, alignment: .leading)
                
                Button(action: {
                    isShowingCreateProject = true
                }) {
                    Label("New Project", systemImage: "plus.circle.fill")
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
            
            if networkManager.projects.isEmpty && networkManager.isLoading {
                ProgressView()
                    .padding()
            } else if networkManager.projects.isEmpty {
                VStack {
                    Text("No projects found")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    
                    Button("Create your first project") {
                        isShowingCreateProject = true
                    }
                    .padding()
                }
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    ForEach(networkManager.projects) { project in
                        ProjectRow(project: project)
                    }
                }
            }
        }
        .onAppear {
            // Fetch projects when view appears
            fetchProjects()
        }
        .sheet(isPresented: $isShowingCreateProject) {
            CreateProjectView()
        }
    }
    
    // Local wrapper function to fetch projects
    private func fetchProjects() {
        let url = URL(string: "http://localhost:8000/projects")!
        
        URLSession.shared.dataTask(with: url) { [weak networkManager] data, response, error in
            guard let networkManager = networkManager else { return }
            
            DispatchQueue.main.async {
                networkManager.isLoading = false
                
                guard error == nil, let data = data else {
                    print("Error fetching projects: \(error?.localizedDescription ?? "Unknown error")")
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let projectsData = json["projects"] as? [[String: Any]] {
                        let projectsJson = try JSONSerialization.data(withJSONObject: projectsData, options: [])
                        let projects = try JSONDecoder().decode([Project].self, from: projectsJson)
                        
                        networkManager.projects = projects
                    }
                } catch {
                    print("Error parsing projects: \(error)")
                }
            }
        }.resume()
    }
}

struct ProjectRow: View {
    let project: Project
    @EnvironmentObject var networkManager: NetworkManager
    @State private var isLoading = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading) {
                    Text(project.name)
                        .font(.headline)
                    
                    Text(project.type.capitalized)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                if isLoading {
                    ProgressView()
                } else {
                    Button("Open") {
                        openProject()
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            
            if !project.description.isEmpty {
                Text(project.description)
                    .font(.body)
                    .lineLimit(2)
            }
            
            HStack {
                Text("Created: \(formattedDate(project.created_at))")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("Last updated: \(formattedDate(project.updated_at))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 8)
    }
    
    private func openProject() {
        isLoading = true
        
        let url = URL(string: "http://localhost:8000/projects/\(project.id)")!
        
        URLSession.shared.dataTask(with: url) { [weak networkManager] data, response, error in
            guard let networkManager = networkManager else { return }
            
            DispatchQueue.main.async {
                self.isLoading = false
                
                guard error == nil, let data = data else {
                    print("Error loading project: \(error?.localizedDescription ?? "Unknown error")")
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let projectData = json["project"] as? [String: Any] {
                        
                        let projectJson = try JSONSerialization.data(withJSONObject: projectData, options: [])
                        let project = try JSONDecoder().decode(Project.self, from: projectJson)
                        
                        // Also load characters if available
                        var characters: [CharacterModel] = []
                        if let charactersData = projectData["characters"] as? [[String: Any]] {
                            let charactersJson = try JSONSerialization.data(withJSONObject: charactersData, options: [])
                            characters = try JSONDecoder().decode([CharacterModel].self, from: charactersJson)
                        }
                        
                        // Also load files if available
                        var files: [ProjectFile] = []
                        if let filesData = projectData["files"] as? [[String: Any]] {
                            let filesJson = try JSONSerialization.data(withJSONObject: filesData, options: [])
                            files = try JSONDecoder().decode([ProjectFile].self, from: filesJson)
                        }
                        
                        // Clear the current session and generate a new one
                        networkManager.sessionId = UUID().uuidString
                        networkManager.currentProject = project
                        networkManager.characters = characters
                        networkManager.files = files
                        
                        print("Project loaded successfully with new session ID: \(networkManager.sessionId)")
                    }
                } catch {
                    print("Error parsing project: \(error)")
                }
            }
        }.resume()
    }
    
    private func formattedDate(_ dateString: String) -> String {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
        
        guard let date = dateFormatter.date(from: dateString) else {
            return dateString
        }
        
        let displayFormatter = DateFormatter()
        displayFormatter.dateStyle = .medium
        displayFormatter.timeStyle = .short
        
        return displayFormatter.string(from: date)
    }
}

struct CreateProjectView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var networkManager: NetworkManager
    
    @State private var projectName = ""
    @State private var projectType = "research"
    @State private var projectDescription = ""
    @State private var errorMessage: String?
    @State private var isLoading = false
    
    let projectTypes = ["research", "songwriting", "book"]
    
    var body: some View {
        NavigationStack {
            Form {
                TextField("Project Name", text: $projectName)
                
                Picker("Project Type", selection: $projectType) {
                    ForEach(projectTypes, id: \.self) { type in
                        Text(type.capitalized)
                    }
                }
                
                Section("Description") {
                    TextEditor(text: $projectDescription)
                        .frame(minHeight: 100)
                }
                
                if let errorMessage = errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                    }
                }
                
                Section {
                    Button("Create Project") {
                        createProject()
                    }
                    .disabled(projectName.isEmpty || isLoading)
                    .frame(maxWidth: .infinity, alignment: .center)
                }
            }
            .navigationTitle("Create Project")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .overlay {
                if isLoading {
                    ProgressView()
                        .padding()
                        .background(.regularMaterial)
                        .cornerRadius(10)
                }
            }
        }
    }
    
    private func createProject() {
        guard !projectName.isEmpty else {
            errorMessage = "Project name cannot be empty"
            return
        }
        
        // Set loading state
        self.isLoading = true
        
        // Prepare the request
        guard let url = URL(string: "http://localhost:8000/projects") else {
            self.errorMessage = "Invalid URL"
            self.isLoading = false
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let json: [String: Any] = [
            "name": projectName,
            "type": projectType,
            "description": projectDescription,
            "metadata": [String: String]()
        ]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            request.httpBody = jsonData
            
            URLSession.shared.dataTask(with: request) { [weak networkManager] data, response, error in
                guard let networkManager = networkManager else { return }
                
                DispatchQueue.main.async {
                    self.isLoading = false
                    
                    if let error = error {
                        self.errorMessage = "Error creating project: \(error.localizedDescription)"
                        return
                    }
                    
                    guard let data = data else {
                        self.errorMessage = "No data received"
                        return
                    }
                    
                    do {
                        if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                           let _ = json["project_id"] as? String {
                            
                            // Update the projects list in NetworkManager
                            let projectsURL = URL(string: "http://localhost:8000/projects")!
                            
                            URLSession.shared.dataTask(with: projectsURL) { data, response, error in
                                guard error == nil, let data = data else { return }
                                
                                do {
                                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                                       let projectsData = json["projects"] as? [[String: Any]] {
                                        let projectsJson = try JSONSerialization.data(withJSONObject: projectsData, options: [])
                                        let projects = try JSONDecoder().decode([Project].self, from: projectsJson)
                                        
                                        DispatchQueue.main.async {
                                            networkManager.projects = projects
                                            self.dismiss()
                                        }
                                    }
                                } catch {
                                    print("Error updating projects after creation: \(error)")
                                    DispatchQueue.main.async {
                                        self.dismiss()
                                    }
                                }
                            }.resume()
                        } else {
                            self.errorMessage = "Invalid response format"
                        }
                    } catch {
                        self.errorMessage = "Error parsing response: \(error.localizedDescription)"
                    }
                }
            }.resume()
        } catch {
            DispatchQueue.main.async {
                self.isLoading = false
                self.errorMessage = "Error encoding project data: \(error.localizedDescription)"
            }
        }
    }
}
