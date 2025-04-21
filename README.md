# LLM Creative Studio

![LLM Creative Studio](https://raw.githubusercontent.com/nickfox137/llm-creative-studio/main/assets/banner.png)

An innovative open-source platform for orchestrating conversations between multiple AI models, with a focus on creative collaboration, structured debates, and advanced role-playing.

## 🌟 Key Features

- **Multi-AI Conversations**: Seamlessly interact with Claude, ChatGPT, and Gemini simultaneously for richer, more diverse insights
- **Structured Collaborative Debates**: Facilitate sophisticated debates between AI models with opening statements, cross-examination, consensus building, and synthesis
- **Character Roleplay**: Assign distinct characters to each AI model for creative storytelling, music composition, and script development
- **Project Management**: Organize conversations, characters, and files into persistent projects
- **Context Integration**: Automatically incorporate relevant document context into conversations
- **Advanced RAG Capabilities**: Utilize local Ollama models for retrieval-augmented generation with project documents
- **Elegant Swift UI**: Clean, intuitive macOS application designed for productive creative work

## 📋 About the Project

LLM Creative Studio was created to explore the untapped potential of multiple AI models working together in structured conversations. Moving beyond simple chat interfaces, this application introduces novel interaction paradigms like multi-agent debates, creative collaborations between character-assigned AI models, and consensus-building workflows.

This project is fully open-source, designed to advance the state of AI collaboration interfaces and provide a robust platform for creative professionals and researchers. The application consists of a Swift frontend and a Python backend, with a focus on modularity and extensibility.

## 🤝 AI Conversation Features

### 💬 Multi-AI Conversations

Interact with Claude, ChatGPT, and Gemini simultaneously, with smart message routing:

- Direct messages to specific AI models using @mentions (`@claude`, `@chatgpt`, `@gemini`)
- Address all models at once for diverse perspectives
- Character-based addressing (e.g., "John, what do you think about...")
- View all responses in a unified conversation flow

### 🎭 Character Roleplay

Transform AI models into specific characters for creative scenarios:

- Assign distinct identities to different models (`/character claude John Lennon`)
- AI models respond in-character, maintaining consistent personas
- Use character-addressing to direct messages naturally
- Create rich, multi-character dialogues for storytelling or scriptwriting

### 🗣️ Structured Debates

The most innovative feature - a structured multi-round debate system:

1. **Opening statements**: Each AI model presents its initial position
2. **Defense & Questions**: Models pose challenging questions to each other
3. **Responses & Final Positions**: Models address questions and refine their positions
4. **Weighted Consensus**: Models allocate percentage points to the most persuasive arguments
5. **Final Synthesis**: A comprehensive summary integrates the strongest elements from all positions

User participation is built-in, with prompts for input after each round to guide the debate or add your own perspectives.

### 🔍 Advanced Research Mode

Optimize for deep research and document analysis:

- Automatically integrate relevant document content into model prompts
- Utilize RAG capabilities for grounded responses on project documents
- Issue structured research queries with specialized formatting
- Combine insights from multiple AI models for comprehensive analysis

## 🧠 Technical Implementation

### System Architecture

The application consists of two main components:

1. **Swift Frontend**: Clean, native macOS application built with SwiftUI
2. **Python Backend**: FastAPI server handling conversation management, LLM interactions, and document processing

Key backend components:

- **ConversationManager**: Orchestrates multi-LLM conversations and command processing
- **DebateManager**: Manages structured debates with intelligent turn-taking
- **CharacterManager**: Handles character assignments and persona-based interactions
- **ProjectManager**: Maintains persistent state for projects, files, and sessions
- **OllamaService**: Provides local RAG capabilities using Qwen2.5 and Arctic models

### Open-Source Foundation

LLM Creative Studio is built on modern open-source technologies:

- **FastAPI**: High-performance Python web framework
- **SwiftUI**: Modern declarative UI framework
- **SQLite**: Lightweight relational database for storage
- **Ollama**: Local AI model management
- **PapaParser**: CSV parsing utilities
- **Langchain**: For document processing and vector operations

## 💭 Example Use Cases

### Creative Collaboration

A songwriter can create a project with three AI characters:

- Claude as "John Lennon"
- ChatGPT as "Paul McCartney"
- Gemini as "George Martin"

The models collaborate on lyrics, melody suggestions, and arrangement ideas, each contributing from their unique stylistic perspective.

### Philosophical Debates

Start a structured debate on a complex topic:

```
/debate "Is consciousness an emergent property of complex systems?"
```

Watch as the models present opening statements, challenge each other with probing questions, synthesize responses, and ultimately build consensus around the strongest arguments.

### Research Deep Dives

Upload research papers to a project and initiate a multi-model analysis:

```
@claude Analyze the methodology section
@chatgpt Evaluate the statistical approach
@gemini Compare these findings with recent literature
```

The platform combines these specialized analyses into a comprehensive review.

## 📦 Getting Started

### Prerequisites

- macOS 15.1+ (Swift application)
- Python 3.10+ (Backend service)
- OpenAI API key (for ChatGPT)
- Anthropic API key (for Claude)
- Google AI Studio API key (for Gemini)
- Recommended: Ollama with qwen2.5:14b-instruct-q8_0 and snowflake-arctic-embed:137m models (for RAG)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nickfox137/llm-creative-studio.git
   cd llm-creative-studio
   ```

2. Install Python dependencies:
   ```bash
   cd python
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the python directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   GOOGLE_API_KEY=your_google_key
   ```

4. Start the backend server:
   ```bash
   python main.py
   ```

5. Open the Swift project in Xcode and build/run the application:
   ```bash
   cd ../swift/LLMCreativeStudio
   open LLMCreativeStudio.xcodeproj
   ```

## 🌱 Contributing

Contributions are welcome! If you're interested in enhancing LLM Creative Studio, here are some areas where you could help:

- Additional LLM integration (Llama, Mistral, etc.)
- Enhanced character management
- New conversation modes
- UI improvements
- Documentation
- Testing

Please feel free to open issues or submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Special thanks to OpenAI, Anthropic, and Google for their powerful AI models
- The open-source community for providing the foundational libraries and frameworks
- All contributors who have helped shape and improve this project

---

*LLM Creative Studio - Orchestrating the future of AI collaboration*