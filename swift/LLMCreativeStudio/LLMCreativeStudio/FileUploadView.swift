// FileUploadView.swift
import SwiftUI
import AppKit
import UniformTypeIdentifiers

struct FileUploadView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var isShowingFileImporter = false
    @State private var selectedFileURL: URL?
    @State private var fileDescription = ""
    @State private var isReference = true
    @State private var isUploading = false
    @State private var errorMessage: String?
    @State private var successMessage: String?
    @State private var processingForRAG = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Title
            Text("File Management")
                .font(.title2)
                .fontWeight(.bold)
            
            // Project check
            if networkManager.currentProject == nil {
                noProjectSelectedView
            } else {
                uploadFormView
                
                Divider()
                
                // File listing
                fileListingView
            }
        }
        .padding()
        .frame(minWidth: 500, minHeight: 300)
        .fileImporter(
            isPresented: $isShowingFileImporter,
            allowedContentTypes: [.pdf, .plainText, .data],
            allowsMultipleSelection: false
        ) { result in
            handleFileImport(result)
        }
    }
    
    private var noProjectSelectedView: some View {
        VStack(spacing: 12) {
            Image(systemName: "folder.badge.questionmark")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("No project selected")
                .font(.headline)
            
            Text("Please select a project to upload files")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .id("noProjectSelectedView")
    }
    
    private var uploadFormView: some View {
        VStack(alignment: .leading, spacing: 12) {
            // File selection button
            HStack {
                Button("Select File") {
                    isShowingFileImporter = true
                }
                .buttonStyle(.borderedProminent)
                
                if let url = selectedFileURL {
                    Text(url.lastPathComponent)
                        .lineLimit(1)
                        .truncationMode(.middle)
                }
            }
            
            // File details
            if selectedFileURL != nil {
                TextField("File Description", text: $fileDescription)
                    .textFieldStyle(.roundedBorder)
                
                Picker("File Type", selection: $isReference) {
                    Text("Reference Material").tag(true)
                    Text("Project Output").tag(false)
                }
                .pickerStyle(.segmented)
                
                Toggle("Process file for RAG after upload", isOn: $processingForRAG)
                    .toggleStyle(.switch)
                
                // Upload button
                Button("Upload") {
                    uploadFile()
                }
                .buttonStyle(.borderedProminent)
                .disabled(selectedFileURL == nil || isUploading)
                .overlay {
                    if isUploading {
                        ProgressView()
                    }
                }
            }
            
            // Status messages
            if let errorMessage = errorMessage {
                Text(errorMessage)
                    .foregroundColor(.red)
                    .font(.caption)
            }
            
            if let successMessage = successMessage {
                Text(successMessage)
                    .foregroundColor(.green)
                    .font(.caption)
            }
        }
    }
    
    private var fileListingView: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Project Files")
                .font(.headline)
            
            if networkManager.files.isEmpty {
                Text("No files available")
                    .foregroundColor(.secondary)
                    .font(.subheadline)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else {
                List {
                    ForEach(networkManager.files) { file in
                        FileRow(file: file)
                    }
                }
                .frame(height: 200)
                .listStyle(.bordered)
                
                Button("Process All Files for RAG") {
                    processAllFilesForRAG()
                }
                .disabled(networkManager.files.isEmpty)
            }
        }
    }
    
    // File import handler
    private func handleFileImport(_ result: Result<[URL], Error>) {
        errorMessage = nil
        successMessage = nil
        
        switch result {
        case .success(let urls):
            guard let url = urls.first else { return }
            
            // Ensure we can access the file
            guard url.startAccessingSecurityScopedResource() else {
                errorMessage = "Unable to access the selected file"
                return
            }
            
            // Store the URL for upload
            selectedFileURL = url
            
            // The filename can be used as the default description
            fileDescription = url.lastPathComponent
            
        case .failure(let error):
            errorMessage = "File selection failed: \(error.localizedDescription)"
        }
    }
    
    // File upload function
    private func uploadFile() {
        guard let projectId = networkManager.currentProject?.id,
              let fileURL = selectedFileURL else {
            return
        }
        
        // Set loading state
        isUploading = true
        errorMessage = nil
        successMessage = nil
        
        // Perform upload
        networkManager.uploadFile(
            projectId: projectId,
            fileURL: fileURL,
            description: fileDescription,
            isReference: isReference
        ) { result in
            DispatchQueue.main.async {
                isUploading = false
                
                switch result {
                case .success(let fileId):
                    successMessage = "File uploaded successfully"
                    
                    // Reset form
                    selectedFileURL?.stopAccessingSecurityScopedResource()
                    selectedFileURL = nil
                    fileDescription = ""
                    
                    // Process for RAG if requested
                    if processingForRAG {
                        processFileForRAG(projectId: projectId, fileId: fileId)
                    }
                    
                    // Reload files
                    networkManager.loadProjectFiles(projectId: projectId)
                    
                case .failure(let error):
                    errorMessage = "Upload failed: \(error.localizedDescription)"
                }
            }
        }
    }
    
    // Process a file for RAG
    private func processFileForRAG(projectId: String, fileId: String) {
        networkManager.processDocumentForRAG(projectId: projectId, documentId: fileId) { result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    successMessage = "File processed for RAG successfully"
                case .failure(let error):
                    errorMessage = "RAG processing failed: \(error.localizedDescription)"
                }
            }
        }
    }
    
    // Process all files for RAG
    private func processAllFilesForRAG() {
        guard let projectId = networkManager.currentProject?.id else {
            return
        }
        
        networkManager.processAllDocumentsForRAG(projectId: projectId) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let results):
                    successMessage = "Processed \(results.processed) files for RAG"
                    if results.failed > 0 {
                        errorMessage = "Failed to process \(results.failed) files"
                    }
                case .failure(let error):
                    errorMessage = "RAG processing failed: \(error.localizedDescription)"
                }
            }
        }
    }
}

struct FileRow: View {
    let file: ProjectFile
    @EnvironmentObject var networkManager: NetworkManager
    @State private var isProcessing = false
    @State private var processingSucceeded = false
    
    var body: some View {
        HStack {
            // File icon
            Image(systemName: fileTypeIcon)
                .foregroundColor(fileTypeColor)
            
            // File info
            VStack(alignment: .leading) {
                Text(fileName)
                    .fontWeight(.medium)
                
                if !file.description.isEmpty {
                    Text(file.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            // File type badge
            Text(file.is_reference ? "Reference" : "Output")
                .font(.caption)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(file.is_reference ? Color.blue.opacity(0.1) : Color.green.opacity(0.1))
                .foregroundColor(file.is_reference ? .blue : .green)
                .cornerRadius(4)
            
            // Process for RAG button
            Button(action: {
                processForRAG()
            }) {
                if isProcessing {
                    ProgressView()
                        .frame(width: 16, height: 16)
                } else if processingSucceeded {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                } else {
                    Image(systemName: "brain")
                        .foregroundColor(.purple)
                }
            }
            .buttonStyle(.borderless)
            .help("Process for RAG")
            
            // Download button
            Button(action: {
                downloadFile()
            }) {
                Image(systemName: "arrow.down.circle")
                    .foregroundColor(.blue)
            }
            .buttonStyle(.borderless)
            .help("Download file")
        }
        .padding(.vertical, 4)
    }
    
    private var fileName: String {
        let path = file.file_path
        return path.split(separator: "/").last?.split(separator: "_").dropFirst().joined(separator: "_") ?? path
    }
    
    private var fileTypeIcon: String {
        switch file.file_type.lowercased() {
        case "pdf":
            return "doc.fill"
        case "text":
            return "doc.text.fill"
        case "markdown":
            return "doc.text.fill"
        case "csv":
            return "tablecells.fill"
        case "image":
            return "photo.fill"
        default:
            return "doc.fill"
        }
    }
    
    private var fileTypeColor: Color {
        switch file.file_type.lowercased() {
        case "pdf":
            return .red
        case "text", "markdown":
            return .blue
        case "csv":
            return .green
        case "image":
            return .orange
        default:
            return .gray
        }
    }
    
    private func processForRAG() {
        guard let projectId = networkManager.currentProject?.id else { return }
        
        isProcessing = true
        processingSucceeded = false
        
        networkManager.processDocumentForRAG(projectId: projectId, documentId: file.id) { result in
            DispatchQueue.main.async {
                isProcessing = false
                
                switch result {
                case .success:
                    processingSucceeded = true
                case .failure:
                    processingSucceeded = false
                }
            }
        }
    }
    
    private func downloadFile() {
        guard let projectId = networkManager.currentProject?.id else { return }
        
        networkManager.downloadFile(projectId: projectId, fileId: file.id) { result in
            // Handle result (already on main thread)
            switch result {
            case .success(let savedURL):
                NSWorkspace.shared.selectFile(savedURL.path, inFileViewerRootedAtPath: "")
            case .failure:
                // Error would be shown by NetworkManager
                break
            }
        }
    }
}