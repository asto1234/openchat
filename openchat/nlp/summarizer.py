"""
NLP Summarization Module
Uses Hugging Face transformers for conversation summarization
Server-side model for generating conversation summaries
"""

from transformers import pipeline, T5ForConditionalGeneration, T5Tokenizer
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ConversationSummarizer:
    """
    Generates summaries of encrypted conversations
    Uses facebook/bart-large-cnn or google/flan-t5-base for abstractive summarization
    """
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        Initialize the summarizer with a pre-trained model
        Models that work well:
        - facebook/bart-large-cnn: Good for news/article summarization
        - google/flan-t5-base: General purpose instruction-following
        - philschmid/bart-large-cnn-samsum: Optimized for dialogue
        """
        self.model_name = model_name
        try:
            self.summarizer = pipeline("summarization", model=model_name, device=0)
            logger.info(f"Loaded summarization model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            # Fallback to smaller model
            self.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
            logger.info("Using fallback model: distilbart-cnn-6-6")
    
    def summarize_conversation(
        self,
        messages: List[str],
        max_length: int = 150,
        min_length: int = 50
    ) -> str:
        """
        Summarize a list of messages from a conversation
        
        Args:
            messages: List of conversation messages
            max_length: Maximum length of summary
            min_length: Minimum length of summary
        
        Returns:
            Summarized conversation
        """
        if not messages:
            return "No messages to summarize."
        
        # Join messages with newlines
        full_conversation = "\n".join(messages)
        
        # Check if conversation is long enough to summarize
        if len(full_conversation.split()) < 50:
            return full_conversation
        
        try:
            summary = self.summarizer(
                full_conversation,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            return summary[0]['summary_text']
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return full_conversation
    
    def extract_key_topics(self, messages: List[str], num_topics: int = 5) -> List[str]:
        """
        Extract key topics/themes from conversation using zero-shot classification
        """
        try:
            classifier = pipeline("zero-shot-classification")
            full_conversation = " ".join(messages)
            
            candidate_topics = [
                "technical discussion",
                "personal matters",
                "work-related",
                "urgent issues",
                "general chat",
                "problem solving",
                "planning",
                "feedback",
                "questions",
                "announcements"
            ]
            
            result = classifier(full_conversation, candidate_topics)
            # Return top topics
            return [label for label, _ in sorted(
                zip(result['labels'], result['scores']),
                key=lambda x: x[1],
                reverse=True
            )[:num_topics]]
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return []
    
    def generate_session_summary(self, messages: List[str]) -> dict:
        """
        Generate comprehensive session summary including:
        - Overall summary
        - Key topics
        - Message count
        - Approximate time span
        """
        if not messages:
            return {
                "summary": "No messages in this session.",
                "topics": [],
                "message_count": 0
            }
        
        summary_text = self.summarize_conversation(messages)
        topics = self.extract_key_topics(messages)
        
        return {
            "summary": summary_text,
            "topics": topics,
            "message_count": len(messages),
            "first_message_preview": messages[0][:100] if messages else "",
            "last_message_preview": messages[-1][:100] if messages else ""
        }


class DialogueSummarizer:
    """
    Specialized summarizer optimized for dialogue/chat conversations
    Uses models fine-tuned on dialogue data
    """
    
    def __init__(self):
        """Initialize dialogue-specific models"""
        try:
            # Try to load dialogue-optimized model
            self.tokenizer = T5Tokenizer.from_pretrained("t5-base")
            self.model = T5ForConditionalGeneration.from_pretrained("t5-base")
            self.use_finetuned = True
        except Exception as e:
            logger.warning(f"Could not load T5 model: {e}")
            self.use_finetuned = False
            self.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
    
    def summarize_dialogue(self, conversation_turns: List[Tuple[str, str]]) -> str:
        """
        Summarize structured dialogue (speaker, message) pairs
        
        Args:
            conversation_turns: List of (speaker, message) tuples
        
        Returns:
            Summarized dialogue
        """
        # Format dialogue for the model
        formatted_dialogue = "\n".join([
            f"{speaker}: {message}"
            for speaker, message in conversation_turns
        ])
        
        if self.use_finetuned:
            inputs = self.tokenizer.encode(
                "summarize: " + formatted_dialogue,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )
            summary_ids = self.model.generate(inputs, max_length=150, min_length=50)
            return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        else:
            result = self.summarizer(formatted_dialogue, max_length=150, min_length=50)
            return result[0]['summary_text']


if __name__ == "__main__":
    # Test the summarizer
    summarizer = ConversationSummarizer()
    
    test_messages = [
        "Hey, how are you doing today?",
        "I'm doing great! Just finished the project",
        "Awesome! Which features did you implement?",
        "I added authentication, database integration, and API endpoints",
        "That's fantastic! How long did it take?",
        "About 3 days of development with testing",
        "Cool! Let's merge it to main branch",
        "Already created a PR, waiting for your review"
    ]
    
    print("Original conversation:")
    for msg in test_messages:
        print(f"  - {msg}")
    
    print("\nGenerated Summary:")
    summary = summarizer.summarize_conversation(test_messages)
    print(f"  {summary}")
    
    print("\nSession Summary:")
    session_summary = summarizer.generate_session_summary(test_messages)
    print(f"  Overall: {session_summary['summary']}")
    print(f"  Topics: {', '.join(session_summary['topics'])}")
    print(f"  Message count: {session_summary['message_count']}")
