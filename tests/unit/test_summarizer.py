"""
Test suite for NLP summarizer
"""

import pytest
import sys
from pathlib import Path

# Add openchat package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from openchat.nlp import ConversationSummarizer


class TestConversationSummarizer:
    """Test NLP summarization"""
    
    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return ConversationSummarizer()
    
    def test_summarizer_initialization(self, summarizer):
        """Test summarizer initialization"""
        assert summarizer is not None
        assert summarizer.summarizer is not None
    
    def test_summarize_simple_conversation(self, summarizer):
        """Test summarization of simple conversation"""
        messages = [
            "Hey, how are you?",
            "I'm doing great!",
            "That's awesome!",
            "Yes, it's a beautiful day"
        ]
        
        summary = summarizer.summarize_conversation(messages)
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_summarize_longer_conversation(self, summarizer):
        """Test summarization of longer conversation"""
        messages = [
            "Hi Alice, did you finish the project?",
            "Almost done! Just fixing the last bug",
            "Great! Which bug was it?",
            "The authentication endpoint was timing out",
            "Did you check the database logs?",
            "Yes, found a slow query that I optimized",
            "Perfect! Let's merge it to main then",
            "Sounds good, I'll create a pull request now"
        ]
        
        summary = summarizer.summarize_conversation(messages)
        assert isinstance(summary, str)
        assert len(summary) > 0
        # Summary should be shorter than original
        total_chars = sum(len(msg) for msg in messages)
        assert len(summary) < total_chars
    
    def test_empty_conversation(self, summarizer):
        """Test summarization of empty conversation"""
        summary = summarizer.summarize_conversation([])
        assert "No messages" in summary
    
    def test_short_conversation(self, summarizer):
        """Test that short conversations return as-is"""
        messages = ["Hello", "Hi"]
        summary = summarizer.summarize_conversation(messages)
        # Short conversations might just be concatenated
        assert len(summary) > 0
    
    def test_extract_key_topics(self, summarizer):
        """Test topic extraction"""
        messages = [
            "We need to fix the bug in authentication",
            "Yes, the login endpoint is broken",
            "I already created a GitHub issue for it",
            "Let's discuss the timeline for fixes",
            "I can start working on it tomorrow"
        ]
        
        topics = summarizer.extract_key_topics(messages)
        assert isinstance(topics, list)
        # Should extract some topics
        assert len(topics) > 0
    
    def test_generate_session_summary(self, summarizer):
        """Test complete session summary generation"""
        messages = [
            "Good morning!",
            "Hey, ready for the standup?",
            "Yes! We shipped the new feature",
            "Awesome! How are the metrics looking?",
            "Great, conversion increased by 15%",
            "That's excellent! Let's celebrate"
        ]
        
        session_summary = summarizer.generate_session_summary(messages)
        
        assert isinstance(session_summary, dict)
        assert 'summary' in session_summary
        assert 'topics' in session_summary
        assert 'message_count' in session_summary
        assert session_summary['message_count'] == len(messages)
        assert isinstance(session_summary['topics'], list)
    
    def test_session_summary_empty(self, summarizer):
        """Test session summary for empty conversation"""
        session_summary = summarizer.generate_session_summary([])
        
        assert isinstance(session_summary, dict)
        assert 'message_count' in session_summary
        assert session_summary['message_count'] == 0


class TestSpecialCases:
    """Test special cases and edge cases"""
    
    @pytest.fixture
    def summarizer(self):
        return ConversationSummarizer()
    
    def test_unicode_messages(self, summarizer):
        """Test summarization with unicode characters"""
        messages = [
            "你好，你好吗？",
            "很好，谢谢",
            "Great! 😀",
            "How are your projects going? 🚀"
        ]
        
        summary = summarizer.summarize_conversation(messages)
        assert isinstance(summary, str)
    
    def test_very_long_messages(self, summarizer):
        """Test summarization with very long messages"""
        long_message = "This is a very long message. " * 100
        messages = [
            long_message,
            "Short reply",
            long_message,
            "Another short one"
        ]
        
        summary = summarizer.summarize_conversation(messages, max_length=200)
        assert len(summary) <= 300  # Some buffer for the model
    
    def test_technical_conversation(self, summarizer):
        """Test summarization of technical conversation"""
        messages = [
            "The API endpoint returns 500 error",
            "Which endpoint? POST /users?",
            "/users/{id}/profile endpoint",
            "I see null pointer exception in logs",
            "Looks like a database connection issue",
            "Yes, connection pool is exhausted",
            "Let's increase the pool size"
        ]
        
        session_summary = summarizer.generate_session_summary(messages)
        assert session_summary['message_count'] == len(messages)
        assert len(session_summary['summary']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
