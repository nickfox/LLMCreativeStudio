# readme.txt

cd /Users/nickfox137/Documents/llm-creative-studio

python3 -m venv venv
source venv/bin/activate
close terminal window to deactivate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

main.py is the first iteration multi-llm chat with Gemini-2.0-Pro-Exp-02-05

lmm-creative-studio.txt is the long chat with gemini 2.0 flash thinking experimental model detailing the requirements for llm creative studio
https://gemini.google.com/app/0980fb4c8f7b5a2c

discussion of architecture and tools

first off, i will always be using macs to run the software we will create. i prefer desktop applications to command line or web apps. I wanted to start off the conversation by deciding what tools we would be using. xcode and swift which would allow us to create a beautiful app and access to all things mac. google AI studio? Python, langchain and other tools which would allow us to take advantage of existing AI integration frameworks. a hybrid of these two, or perhaps something entirely different that you could recommnend. 

i am open to all suggestions and to be very clear, i'm not tied down to any language, programming environment or framework. you see from my initital conversation i had earlier today with gemini where i'm going with this and what i hope to accomplish.

please advise.

*******************

first off, your plan sounds excellent. and here are a few things that will help me: 

1. every file that we write together should have a comment at the top of the file with the full path and file name

ie.
# /Users/nickfox137/Documents/llm-creative-studio/example.swift
# /Users/nickfox137/Documents/llm-creative-studio/example.py

this is immensely helpful and this is the actual root directory for the project:

/Users/nickfox137/Documents/llm-creative-studio/

and the top level directory structure

llm-creative-studio/
├── swift/
└── python/

the python directory will have the venv and python code, feel free to suggest an upper level directory structure for other things
like langchain, etc.

2. please include all imports when writing files. (for some reason deepseek felt import statements were not necessary...)

3. when giving me code files or updates, plese just give me the entire file instead of code snippets. (i am 64 and prefer not to hunt and peck through code files)

4. if we are starting off by continuing work on main.py, could you please include code for claude. these will be our three LLMs:

gemini, chatgpt and claude.

5. "Swift, Storyboard or SwiftUI – your preference, but Storyboard might be easier if you're more familiar with older Xcode"

i have no interest at all in backwards compatibility. i think swiftUI would be the best going forward.

*************

claude cheapest model

claude-3-5-haiku-20241022

https://docs.anthropic.com/en/docs/about-claude/models

**************

AIs in the chat need to ask clarifying questions and challenge other AIs!!!!!!!!!!!!!!!!!!!!!!!!!!!!


is RAG appropriate now with small chunking? is it needed?
https://www.youtube.com/watch?v=iK9wefkOjkY

would sqlite or another store be better for better accuracy. since i will not have lots of data, is there something that takes entire pdfs or pdf broken up by chapter?clear

******************

LLMCreativeStudio is the app name

com.websmithing.LLMCreativeStudio is the bundle indentifier

need more error handling and logging in the swift code

%%%%%%%%%%%%%%%%%%%%%%%%%%


i've broken out the app into other files and everything is working correctly. i've also put the application under version control. its on github in a private repo called "LLMCreativeStudio". at the end of each iteration can you please give me the command (from my mac terminal) to push the latest iteration and also, why don't we call each iteration by a number. ie, 0.1, 0.2. 0.3 etc. i'm not sure what iteration we are on but, let's start numbering them so that we can refer back easily to a past iteration. Please figure out what number iteration we are on and let me know the number.

within the chat app, please remove the 3 buttons from the app (gemini, chatgpt, claude) and instead, i would like to "send" to one of the AIs when i mention them by name in my chat text. their names are below preceeded by the @ sign. (ie, Nick -> "could i get a summary of that, @g", "hey @o, can you please check the web for me.")

@all = send message to all 3
@a and @claude = send to claude
@c and @chatgpt = send to chatgpt
@g and @gemini = send to gemini

no send button

textbox goes all the way across the app with padding, and the text box should be 3 lines high. in the textbox, if i press enter then please send. if i press shift-enter, then just go down to the next line.

here is the challenge now, i would prefer if we just used sqlite instead of a json file. i've been using sqlite since about 2000 and i think it's a more robust, and professional way to handle this. plus i like it. also, let gets langchain involved, it think that help with some of the upcoming functionality. if you think it's a good idea to break these up into two iterations instead of one, let me know. but i think this is a good direction, let me know if you agree. take advantage of all of langchain's abilities. currently we are storing keywords for retrieval. is that the best way in a semantic world?

i want to be able to drag and drop a pdf on to the app chat window, doing that then causes this:

a. create a new nick message bubble, always give the title of document ("Agentic Reasoning: Reasoning LLMs with Tools for the Deep Research") if applicable, and also the actual name of the file ("agentic-reasoning.pdf"), if it's a paper from a scientic journal, give the abstract and conclusion also directly from the paper.
b. send the pdf to the 3 llms for analysis, summary and own conclusion (not the conclusion in the paper, your own opinion), relevant keywords, section titles if applicable, this will be used to create a record in sqlite for later retrieval, and all other information that you need about the document.
c. puts the pdf into the libary directory (make sure watchdog is running as we discussed above in "library" directory)
d. each llm just gives summary and own conclusion in chat window
e. put the record into sqlite

when all the summaries/conclusions have arrived, then we will begin a "chat with PDF" session. i want each to ask questions. ask clarifying questions to me and to the other LLMs. answer questions in a natural round-robin way, and if llm started with or was assigned a task or persona, make sure that questions pertaining to that AI is relevant. and if a question is asked, the AI to whom the question is most relevant should answer. Make observations, provide alternative views. discuss the ideas within the pdf and the conclusions. discuss the plausibility of the conclusion and the experiment. things like that, please provide more ideas. i want this to be very much like 4 people sitting together and discussing a pdf, a research paper for instance. make it feel natural with good flow of discussion.

i'm sure chatting with PDFs has been well documented somewhere. i'm attaching the first pdf (agentic-reasoning.pdf), i would like you to analyze it summarize for me, please. this will be the pdf i drop onto the application chat window. this is a very new paper, is there anything in there that would make you want to change your architecture? lets discuss this and please advise.  


^^^^^^^^^^^^^

langchain next

UnstructuredPDFLoader
RecursiveCharacterTExtSplitter

