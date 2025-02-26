"""
Debate Manager Module

This module handles structured multi-round debates between multiple LLMs,
implementing a dynamic collaborative debate system with natural turn-taking,
cross-examination, and weighted consensus.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import json

class DebateState(Enum):
    """
    Enumeration of possible states in the debate process.
    """
    IDLE = 0
    ROUND_1_OPENING = 1
    ROUND_2_QUESTIONING = 2
    ROUND_3_RESPONSES = 3
    ROUND_4_CONSENSUS = 4
    FINAL_SYNTHESIS = 5
    COMPLETE = 6

class DebateManager:
    """
    Manages structured multi-round debates between multiple LLMs.
    
    Implements a collaborative debate system with:
    1. Opening statements
    2. Defense & cross-examination
    3. Responses & final positions
    4. Weighted consensus voting
    5. Synthesis of results
    
    Attributes:
        conversation_manager (ConversationManager): The parent conversation manager
        state (DebateState): Current state of the debate
        topic (str): The debate topic
        rounds (int): Number of rounds in the debate
        current_speaker (str): Current active speaker (LLM name)
        speaker_order (List[str]): Order of speakers in the debate
        completed_speakers (Set[str]): Speakers who have completed their turn in the current round
        questions (Dict[str, Dict[str, str]]): Tracks questions asked by each LLM to others
        final_positions (Dict[str, str]): Final position statements from each LLM
        consensus_scores (Dict[str, Dict[str, int]]): Percentage allocations from each LLM
        debate_history (List[Dict]): Complete history of the debate
    """
    
    def __init__(self, conversation_manager):
        """
        Initialize a new DebateManager.
        
        Args:
            conversation_manager: The parent conversation manager
        """
        self.cm = conversation_manager
        self.state = DebateState.IDLE
        self.topic = ""
        self.rounds = 0
        self.current_speaker = None
        self.speaker_order = []
        self.completed_speakers = set()
        self.questions = {}  # Format: {from_llm: {to_llm: question}}
        self.final_positions = {}  # Format: {llm: final_position}
        self.consensus_scores = {}  # Format: {from_llm: {to_llm: percentage}}
        self.debate_history = []  # History of all debate messages
        self.waiting_for_user = False  # Flag to indicate if waiting for user input
        self.user_inputs = {}  # Track user inputs for each round
        
    async def start_debate(self, topic: str) -> List[Dict[str, Any]]:
        """
        Start a new debate on the specified topic with the fixed format.
        
        Args:
            topic (str): The topic to debate
            
        Returns:
            List[Dict[str, Any]]: Initial system message about the debate
        """
        self.topic = topic
        self.rounds = 4  # Fixed format with 4 rounds plus synthesis
        self.state = DebateState.ROUND_1_OPENING
        
        # Reset debate state
        self.questions = {}
        self.final_positions = {}
        self.consensus_scores = {}
        self.debate_history = []
        self.completed_speakers = set()
        
        # Determine which LLMs are participating
        self.speaker_order = list(self.cm.active_roles.keys()) 
        if not self.speaker_order:
            self.speaker_order = ["claude", "chatgpt", "gemini"]
        
        # Create system message announcing debate start
        system_message = {
            "sender": "system",
            "content": f"Starting {self.rounds}-round collaborative debate on: {topic}\n\n"
                      f"Round 1: Opening statements\n"
                      f"Round 2: Defense & questions\n"
                      f"Round 3: Responses & final positions\n"
                      f"Round 4: Weighted consensus\n"
                      f"Final: Synthesis of results",
            "is_system": True,
            "debate_round": 0,
            "debate_state": self.state.name
        }
        
        # Add to debate and conversation history
        self.debate_history.append(system_message)
        self.cm.conversation_history.append(system_message)
        
        # Start the debate process
        next_responses = await self.advance_debate()
        
        # Return system message plus initial responses
        return [system_message] + next_responses
    
    async def advance_debate(self) -> List[Dict[str, Any]]:
        """
        Advance the debate to the next speaker or round.
        
        Handles the state machine logic for progressing through debate rounds,
        generating appropriate prompts for each round and collecting responses.
        
        Returns:
            List[Dict[str, Any]]: Response messages from the current step
        """
        responses = []
        
        if self.state == DebateState.IDLE:
            return []
            
        # Handle based on current state
        if self.state in [DebateState.ROUND_1_OPENING, DebateState.ROUND_2_QUESTIONING, 
                         DebateState.ROUND_3_RESPONSES, DebateState.ROUND_4_CONSENSUS]:
            
            # Find next speaker who hasn't spoken in this round
            next_speaker = None
            for speaker in self.speaker_order:
                if speaker not in self.completed_speakers:
                    next_speaker = speaker
                    break
                    
            if next_speaker:
                # Generate prompt for current round and speaker
                prompt = self.generate_round_prompt(next_speaker)
                
                # Get response from the current LLM
                response_content = await self.cm.generate_llm_response(
                    next_speaker, 
                    prompt
                )
                
                # Process the response based on the current round
                if self.state == DebateState.ROUND_2_QUESTIONING:
                    # Extract questions from the response
                    self.extract_questions(next_speaker, response_content)
                elif self.state == DebateState.ROUND_3_RESPONSES:
                    # Store final position
                    self.final_positions[next_speaker] = response_content
                elif self.state == DebateState.ROUND_4_CONSENSUS:
                    # Extract consensus scores
                    self.extract_consensus_scores(next_speaker, response_content)
                
                # Format the response with round/speaker info
                response = {
                    "sender": next_speaker,
                    "content": response_content,
                    "debate_round": self.state.value,
                    "debate_state": self.state.name,
                    "speaker_index": len(self.completed_speakers) + 1,
                    "total_speakers": len(self.speaker_order)
                }
                
                # If the LLM has a character assigned, update the sender
                character = self.cm.character_manager.get_character_for_llm(next_speaker)
                if character:
                    response["character"] = character.character_name
                
                # Add to debate and conversation history
                self.debate_history.append(response)
                self.cm.conversation_history.append(response)
                
                # Mark speaker as completed for this round
                self.completed_speakers.add(next_speaker)
                responses.append(response)
                
                # If all speakers have completed, get next round
                if len(self.completed_speakers) == len(self.speaker_order):
                    # Reset completed speakers for next round
                    self.completed_speakers = set()
                    
                    # Advance to next round if we haven't reached the end
                    round_limit = min(self.rounds, 4)
                    if self.state.value < round_limit:
                        # Advance to next round
                        self.state = DebateState(self.state.value + 1)
                        
                        # Add round transition system message
                        round_message = {
                            "sender": "system",
                            "content": f"Beginning Round {self.state.value}: {self.state.name.replace('_', ' ').title()}",
                            "is_system": True,
                            "debate_round": self.state.value,
                            "debate_state": self.state.name
                        }
                        
                        self.debate_history.append(round_message)
                        self.cm.conversation_history.append(round_message)
                        responses.append(round_message)
                        
                        # Continue to the next round if not consensus
                        if self.state != DebateState.FINAL_SYNTHESIS:
                            next_responses = await self.advance_debate()
                            responses.extend(next_responses)
                    else:
                        # Move to final synthesis after reaching round limit
                        self.state = DebateState.FINAL_SYNTHESIS
                        synthesis_response = await self.generate_synthesis()
                        responses.append(synthesis_response)
                        # Mark debate as complete
                        self.state = DebateState.COMPLETE
                
            else:
                # Should never reach here if logic is correct
                logging.error("No next speaker found but not all speakers completed")
                self.state = DebateState.COMPLETE
                
        elif self.state == DebateState.FINAL_SYNTHESIS:
            # Generate synthesis
            synthesis_response = await self.generate_synthesis()
            responses.append(synthesis_response)
            
            # Mark debate as complete
            self.state = DebateState.COMPLETE
            
        return responses
    
    def generate_round_prompt(self, speaker: str) -> str:
        """
        Generate the appropriate prompt for the current debate state and speaker.
        
        Creates detailed, context-appropriate prompts for each round of the debate,
        customized for the current speaker and incorporating previous contributions.
        
        Args:
            speaker (str): The LLM that will be responding
            
        Returns:
            str: Formatted prompt text
        """
        # Get character name if available
        character = self.cm.character_manager.get_character_for_llm(speaker)
        character_name = character.character_name if character else speaker.capitalize()
        
        # Get other participants
        other_speakers = [s for s in self.speaker_order if s != speaker]
        other_names = []
        for s in other_speakers:
            other_char = self.cm.character_manager.get_character_for_llm(s)
            other_names.append(other_char.character_name if other_char else s.capitalize())
        
        # Start with the debate topic
        prompt = f"DEBATE TOPIC: {self.topic}\n\n"
        
        if self.state == DebateState.ROUND_1_OPENING:
            prompt += f"""
[DEBATE ROUND 1: OPENING STATEMENT]

You are {character_name} participating in a collaborative intellectual exploration with other AI systems. This is not a competitive debate but rather a joint search for the most nuanced understanding.

Present your initial position on this topic in 2-3 paragraphs. Focus on:
1. Your core thesis or perspective
2. Key supporting evidence or reasoning
3. Any important nuances or qualifications

Be clear and concise. You'll have an opportunity to engage with other perspectives in subsequent rounds.
"""

        elif self.state == DebateState.ROUND_2_QUESTIONING:
            # Include previous statements for reference
            prompt += f"""
[DEBATE ROUND 2: DEFENSE & QUESTIONS]

Having heard all opening statements, this round has three components:

PART 1 - REFLECTION (1 paragraph):
Briefly defend or refine your initial position. If you see merit in another participant's argument that changes your thinking, acknowledge this explicitly.

PART 2 - DIRECTED QUESTIONS:
You must ask ONE specific, focused question to each other participant about their position:
"""
            # Add previous statements and request for questions
            for other_speaker, other_name in zip(other_speakers, other_names):
                # Find their opening statement
                opening = self.find_statement(other_speaker, DebateState.ROUND_1_OPENING)
                if opening:
                    prompt += f"\n{other_name}'s opening statement: \"{opening}\"\n"
                    prompt += f"TO {other_name}: [Ask a question that probes a potential weakness, requests clarification, or explores an interesting implication of their argument]\n\n"
            
            prompt += """
PART 3 - POINTS OF AGREEMENT (1-2 sentences):
Identify at least one aspect of another participant's position that you find particularly compelling or persuasive.

Your response should show intellectual honesty - be willing to acknowledge strong points made by others and weaknesses in your own position if they exist.
"""

        elif self.state == DebateState.ROUND_3_RESPONSES:
            prompt += f"""
[DEBATE ROUND 3: RESPONSES & FINAL POSITION]

PART 1 - ANSWER DIRECTED QUESTIONS (1-2 paragraphs per question):
Respond to the specific questions directed to you:
"""
            # Include questions directed at this speaker
            for other_speaker, other_name in zip(other_speakers, other_names):
                if other_speaker in self.questions and speaker in self.questions[other_speaker]:
                    question = self.questions[other_speaker][speaker]
                    prompt += f"\nFROM {other_name}: \"{question}\"\nYour response: [Provide a thoughtful, honest answer]\n"
            
            prompt += """
PART 2 - FINAL POSITION (2 paragraphs):
Present your final position on the topic, incorporating insights from the discussion. Be sure to:
- Address how your thinking may have evolved
- Integrate valuable points raised by others
- Present your strongest case with nuance and precision

Focus on clarity and intellectual honesty rather than simply defending your initial position.
"""

        elif self.state == DebateState.ROUND_4_CONSENSUS:
            prompt += f"""
[DEBATE ROUND 4: WEIGHTED CONSENSUS]

Now that all participants have presented their final positions, your task is to distribute 100 percentage points across all positions (including your own) based on their persuasiveness, evidence quality, and logical coherence.

This is not about "winning" but about recognizing the strongest elements of each position. Your total must equal exactly 100%.

PERCENTAGE ALLOCATIONS:
"""
            # List all speakers for allocation
            for s in self.speaker_order:
                char = self.cm.character_manager.get_character_for_llm(s)
                name = char.character_name if char else s.capitalize()
                prompt += f"{name}'s position: __% \n"
            
            prompt += """
JUSTIFICATION (2-3 sentences for each allocation):
Briefly explain your reasoning for each percentage allocation, focusing on the specific strengths or limitations of each position.

Remember that intellectual honesty is paramount - you should allocate percentages based on argument strength, not loyalty to your own position.
"""

        return prompt
    
    async def generate_synthesis(self) -> Dict[str, Any]:
        """
        Generate a final synthesis of the debate based on consensus scores.
        
        Uses Claude 3 in thinking mode to analyze the final positions and weighting
        to create a nuanced integration of the debate's insights.
        
        Returns:
            Dict[str, Any]: Synthesis response message
        """
        # Prepare a system message announcing the synthesis
        system_message = {
            "sender": "system",
            "content": "Generating final synthesis based on weighted consensus scores...",
            "is_system": True,
            "debate_round": 5,
            "debate_state": "FINAL_SYNTHESIS"
        }
        
        # Add to histories
        self.debate_history.append(system_message)
        self.cm.conversation_history.append(system_message)
        
        # Compile the consensus scores for the prompt
        consensus_summary = "CONSENSUS SCORES:\n"
        avg_scores = self.calculate_average_scores()
        
        for speaker in self.speaker_order:
            name = self.cm.llm_to_character.get(speaker, speaker.capitalize())
            score = avg_scores.get(speaker, 0)
            consensus_summary += f"Position of {name}: {score}%\n"
        
        # Get final positions for each speaker
        positions_summary = "FINAL POSITIONS:\n"
        for speaker in self.speaker_order:
            name = self.cm.llm_to_character.get(speaker, speaker.capitalize())
            position = self.final_positions.get(speaker, "No final position provided")
            positions_summary += f"{name}'s position:\n\"{position}\"\n\n"
        
        # Create the synthesis prompt
        synthesis_prompt = f"""
[FINAL SYNTHESIS]

You will now generate a final synthesis of this debate on "{self.topic}" based on all participants' final positions and their weighted consensus scores.

Each AI participant has allocated percentage points to indicate which arguments they found most persuasive:

{consensus_summary}

{positions_summary}

Based on these allocations and the content of the final positions, create a synthesis that:

1. Weighs each perspective according to its consensus score
2. Identifies the strongest elements from each position
3. Creates an integrated view that acknowledges tensions or unresolved questions
4. Highlights areas of consensus among all participants
5. Suggests potential directions for further exploration

Your synthesis should not simply average positions but create a higher-order integration that captures the most valuable insights from the collaborative exploration.
"""
        
        # Get the synthesis from Claude (preferably) or another available LLM
        synthesizer = "claude" if "claude" in self.speaker_order else self.speaker_order[0]
        synthesis_content = await self.cm.generate_llm_response(
            synthesizer,
            synthesis_prompt,
            use_thinking_mode=True  # Use Claude's thinking mode if available
        )
        
        # Create the synthesis response
        synthesis_response = {
            "sender": "synthesis",
            "content": synthesis_content,
            "debate_round": 5,
            "debate_state": "FINAL_SYNTHESIS",
            "is_synthesis": True
        }
        
        # Add to histories
        self.debate_history.append(synthesis_response)
        self.cm.conversation_history.append(synthesis_response)
        
        return synthesis_response
    
    def extract_questions(self, speaker: str, response: str) -> None:
        """
        Extract questions from a Round 2 response.
        
        Uses simple heuristics to identify questions directed at specific participants.
        A more robust implementation could use NLP techniques for better extraction.
        
        Args:
            speaker (str): The LLM that asked the questions
            response (str): The response text containing questions
        """
        self.questions[speaker] = {}
        
        # Get other participants
        other_speakers = [s for s in self.speaker_order if s != speaker]
        
        for other in other_speakers:
            other_char = self.cm.character_manager.get_character_for_llm(other)
            other_name = other_char.character_name if other_char else other.capitalize()
            
            # Look for sections addressed to this participant
            # Basic approach: Find "TO [name]:" and capture the text after it
            marker = f"TO {other_name}:"
            if marker in response:
                parts = response.split(marker, 1)
                if len(parts) > 1:
                    question_section = parts[1].strip()
                    
                    # Extract until the next section or end
                    end_markers = [f"TO ", "PART ", "\n\n"]
                    for end_marker in end_markers:
                        if end_marker in question_section:
                            question_section = question_section.split(end_marker, 1)[0].strip()
                    
                    self.questions[speaker][other] = question_section
            else:
                # Fallback for less structured responses
                # Try to find sentences containing the participant's name followed by a question mark
                sentences = response.split(". ")
                for i, sentence in enumerate(sentences):
                    if other_name in sentence and "?" in sentence:
                        self.questions[speaker][other] = sentence.strip()
                        break
                    elif other_name in sentence and i+1 < len(sentences) and "?" in sentences[i+1]:
                        self.questions[speaker][other] = f"{sentence}. {sentences[i+1]}".strip()
                        break
        
        # Log the extracted questions
        for other, question in self.questions[speaker].items():
            logging.info(f"Extracted question from {speaker} to {other}: {question[:50]}...")
    
    def extract_consensus_scores(self, speaker: str, response: str) -> None:
        """
        Extract consensus scores from a Round 4 response.
        
        Parses percentage allocations from the response text.
        
        Args:
            speaker (str): The LLM that provided the scores
            response (str): The response text containing percentage allocations
        """
        self.consensus_scores[speaker] = {}
        
        # Look for lines with percentage allocations
        # Format: "[Name]'s position: XX%"
        for other in self.speaker_order:
            other_char = self.cm.character_manager.get_character_for_llm(other)
            other_name = other_char.character_name if other_char else other.capitalize()
            
            # Regular percentage format
            markers = [
                f"{other_name}'s position: ",
                f"{other_name}: ",
                f"{other_name} - "
            ]
            
            for marker in markers:
                if marker in response:
                    parts = response.split(marker, 1)
                    if len(parts) > 1:
                        # Extract the percentage
                        score_text = parts[1].strip().split("%", 1)[0].strip()
                        
                        # Handle any text before the number
                        score_text = ''.join(c for c in score_text if c.isdigit() or c == '.')
                        
                        try:
                            score = int(float(score_text))
                            self.consensus_scores[speaker][other] = score
                            break
                        except ValueError:
                            # Try to find just a number
                            import re
                            match = re.search(r'\d+', score_text)
                            if match:
                                try:
                                    score = int(match.group())
                                    self.consensus_scores[speaker][other] = score
                                    break
                                except ValueError:
                                    pass
        
        # Validate total is close to 100%
        total = sum(self.consensus_scores[speaker].values())
        if total < 95 or total > 105:
            logging.warning(f"Consensus scores from {speaker} sum to {total}, not 100")
            
            # Normalize to 100% if we have some values
            if total > 0:
                for other in self.consensus_scores[speaker]:
                    self.consensus_scores[speaker][other] = int(
                        (self.consensus_scores[speaker][other] / total) * 100
                    )
        
        logging.info(f"Extracted consensus scores from {speaker}: {self.consensus_scores[speaker]}")
    
    def is_waiting_for_user(self) -> bool:
        """
        Check if the debate is currently waiting for user input.
        
        Returns:
            bool: True if waiting for user input, False otherwise
        """
        return getattr(self, 'waiting_for_user', False)
        
    def calculate_average_scores(self) -> Dict[str, int]:
        """
        Calculate average consensus scores across all participants.
        
        Returns:
            Dict[str, int]: Average score for each participant
        """
        avg_scores = {}
        
        # Initialize with zeros
        for speaker in self.speaker_order:
            avg_scores[speaker] = 0
        
        # Sum up all scores
        score_count = {}
        for from_speaker, scores in self.consensus_scores.items():
            for to_speaker, score in scores.items():
                if to_speaker not in score_count:
                    score_count[to_speaker] = 0
                avg_scores[to_speaker] = avg_scores.get(to_speaker, 0) + score
                score_count[to_speaker] += 1
        
        # Calculate averages
        for speaker in avg_scores:
            if speaker in score_count and score_count[speaker] > 0:
                avg_scores[speaker] = int(avg_scores[speaker] / score_count[speaker])
        
        return avg_scores
    
    def find_statement(self, speaker: str, state: DebateState) -> str:
        """
        Find a statement from a specific speaker in a specific debate state.
        
        Args:
            speaker (str): The LLM to find a statement from
            state (DebateState): The debate state to search in
            
        Returns:
            str: The found statement, or empty string if not found
        """
        for msg in self.debate_history:
            if msg.get("sender") == speaker and msg.get("debate_state") == state.name:
                return msg.get("content", "")
        return ""
