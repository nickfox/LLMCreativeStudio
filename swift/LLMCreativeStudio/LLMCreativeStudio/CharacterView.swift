// /Users/nickfox137/Documents/llm-creative-studio/swift/LLMCreativeStudio/LLMCreativeStudio/CharacterView.swift

import SwiftUI

struct CharacterView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var isShowingAddCharacter = false
    
    var body: some View {
        VStack {
            HStack {
                Text("Characters")
                    .font(.title)
                    .fontWeight(.bold)
                    .frame(maxWidth: .infinity, alignment: .leading)
                
                if networkManager.currentProject != nil {
                    Button(action: {
                        isShowingAddCharacter = true
                    }) {
                        Label("Add Character", systemImage: "person.badge.plus")
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding([.horizontal, .top])
            
            if networkManager.isLoading {
                ProgressView()
                    .padding()
            } else if networkManager.characters.isEmpty {
                VStack {
                    if networkManager.currentProject == nil {
                        Text("No project selected")
                            .font(.headline)
                            .foregroundColor(.secondary)
                    } else {
                        Text("No characters defined")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Button("Add your first character") {
                            isShowingAddCharacter = true
                        }
                        .padding()
                    }
                }
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    ForEach(networkManager.characters) { character in
                        CharacterRow(character: character)
                    }
                }
            }
        }
        .sheet(isPresented: $isShowingAddCharacter) {
            AddCharacterView()
        }
    }
}

struct CharacterRow: View {
    let character: CharacterModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading) {
                    Text(character.character_name)
                        .font(.headline)
                    
                    Text("Played by: \(character.llm_name.capitalized)")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Image(systemName: getLLMIcon(for: character.llm_name))
                    .foregroundColor(getLLMColor(for: character.llm_name))
                    .imageScale(.large)
            }
            
            if !character.background.isEmpty {
                Text(character.background)
                    .font(.body)
                    .lineLimit(3)
                    .padding(.top, 4)
            }
        }
        .padding(.vertical, 8)
    }
    
    private func getLLMIcon(for llmName: String) -> String {
        switch llmName.lowercased() {
        case "claude":
            return "a.circle.fill"
        case "chatgpt":
            return "c.circle.fill"
        case "gemini":
            return "g.circle.fill"
        default:
            return "questionmark.circle.fill"
        }
    }
    
    private func getLLMColor(for llmName: String) -> Color {
        switch llmName.lowercased() {
        case "claude":
            return .purple
        case "chatgpt":
            return .green
        case "gemini":
            return .blue
        default:
            return .gray
        }
    }
}

struct AddCharacterView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var networkManager: NetworkManager
    
    @State private var characterName = ""
    @State private var llmName = "claude"
    @State private var background = ""
    @State private var errorMessage: String?
    @State private var isLoading = false
    
    let llmOptions = ["claude", "chatgpt", "gemini"]
    
    var body: some View {
        NavigationStack {
            Form {
                TextField("Character Name", text: $characterName)
                
                Picker("Played by", selection: $llmName) {
                    ForEach(llmOptions, id: \.self) { llm in
                        Text(llm.capitalized)
                    }
                }
                
                Section("Character Background (Optional)") {
                    TextEditor(text: $background)
                        .frame(minHeight: 100)
                }
                
                if let errorMessage = errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                    }
                }
                
                Section {
                    Button("Add Character") {
                        addCharacter()
                    }
                    .disabled(characterName.isEmpty || isLoading || networkManager.currentProject == nil)
                    .frame(maxWidth: .infinity, alignment: .center)
                }
            }
            .navigationTitle("Add Character")
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
    
    private func addCharacter() {
        guard !characterName.isEmpty else {
            errorMessage = "Character name cannot be empty"
            return
        }
        
        guard let projectId = networkManager.currentProject?.id else {
            errorMessage = "No project selected"
            return
        }
        
        isLoading = true
        
        // Prepare the URL and request
        guard let url = URL(string: "http://localhost:8000/projects/\(projectId)/characters") else {
            errorMessage = "Invalid URL"
            isLoading = false
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
            
            URLSession.shared.dataTask(with: request) { [weak networkManager] data, response, error in
                guard let networkManager = networkManager else { return }
                
                DispatchQueue.main.async {
                    self.isLoading = false
                    
                    if let error = error {
                        self.errorMessage = "Error adding character: \(error.localizedDescription)"
                        return
                    }
                    
                    guard let data = data else {
                        self.errorMessage = "No data received"
                        return
                    }
                    
                    do {
                        if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                           let _ = json["character_id"] as? String {
                            
                            // Refresh the project to update characters list
                            guard let projectId = networkManager.currentProject?.id else {
                                self.dismiss()
                                return
                            }
                            
                            let projectURL = URL(string: "http://localhost:8000/projects/\(projectId)")!
                            
                            URLSession.shared.dataTask(with: projectURL) { data, response, error in
                                guard error == nil, let data = data else {
                                    DispatchQueue.main.async {
                                        self.dismiss()
                                    }
                                    return
                                }
                                
                                do {
                                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                                       let projectData = json["project"] as? [String: Any] {
                                        
                                        // Load characters if available
                                        if let charactersData = projectData["characters"] as? [[String: Any]] {
                                            let charactersJson = try JSONSerialization.data(withJSONObject: charactersData, options: [])
                                            let characters = try JSONDecoder().decode([CharacterModel].self, from: charactersJson)
                                            
                                            DispatchQueue.main.async {
                                                networkManager.characters = characters
                                                self.dismiss()
                                            }
                                        } else {
                                            DispatchQueue.main.async {
                                                self.dismiss()
                                            }
                                        }
                                    } else {
                                        DispatchQueue.main.async {
                                            self.dismiss()
                                        }
                                    }
                                } catch {
                                    print("Error refreshing characters: \(error)")
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
                self.errorMessage = "Error encoding character data: \(error.localizedDescription)"
            }
        }
    }
}
