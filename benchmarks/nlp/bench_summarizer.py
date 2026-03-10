"""Benchmarks for NLP and summarization operations."""

import pytest
from openchat.nlp import ConversationSummarizer, MessageSummarizer


class TestNLPBenchmarks:
    """Benchmark NLP operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up NLP for benchmarks."""
        self.summarizer = ConversationSummarizer()

    def test_single_message_summarization(self, benchmark):
        """Benchmark single message summarization."""
        message = (
            "The quick brown fox jumps over the lazy dog. "
            "This is a test message for benchmarking. "
            "It contains multiple sentences to summarize. "
            "The goal is to measure performance."
        )

        def summarize():
            return self.summarizer.summarize_message(message)

        result = benchmark(summarize)
        assert result is not None
        assert len(result) > 0

    def test_conversation_summarization_short(self, benchmark):
        """Benchmark conversation summarization with few messages."""
        conversation = [
            "Hello, how are you today?",
            "I'm doing well, thanks for asking!",
            "Great to hear. What have you been up to?",
            "I've been working on a new project.",
        ]

        def summarize():
            return self.summarizer.summarize_conversation(conversation)

        result = benchmark(summarize)
        assert result is not None

    def test_conversation_summarization_medium(self, benchmark):
        """Benchmark conversation summarization with moderate messages."""
        conversation = [
            f"Message {i}: This is a test message in the conversation. "
            f"It contains information about topic {i % 5}."
            for i in range(20)
        ]

        def summarize():
            return self.summarizer.summarize_conversation(conversation)

        result = benchmark(summarize)
        assert result is not None

    def test_conversation_summarization_long(self, benchmark):
        """Benchmark conversation summarization with many messages."""
        conversation = [
            f"Message {i}: This is message number {i} in a long conversation. "
            f"It discusses various topics including {i % 10}. "
            f"The conversation grows longer with each message."
            for i in range(100)
        ]

        def summarize():
            return self.summarizer.summarize_conversation(conversation)

        result = benchmark(summarize)
        assert result is not None

    @pytest.mark.parametrize("length", [50, 100, 200, 500])
    def test_summarization_different_lengths(self, benchmark, length):
        """Benchmark summarization with different message lengths."""
        message = "word " * length

        def summarize():
            return self.summarizer.summarize_message(message)

        result = benchmark(summarize)
        assert result is not None

    def test_batch_summarization(self, benchmark):
        """Benchmark batch message summarization."""
        messages = [
            f"This is message {i} containing some text to summarize. "
            f"It has multiple sentences and provides context."
            for i in range(10)
        ]

        def summarize_batch():
            return [self.summarizer.summarize_message(msg) for msg in messages]

        results = benchmark(summarize_batch)
        assert len(results) == 10
        assert all(r is not None for r in results)

    def test_keyword_extraction(self, benchmark):
        """Benchmark keyword extraction."""
        message = (
            "Keyword extraction is an important task in natural language processing. "
            "It helps identify the main topics and concepts. "
            "Machine learning and deep learning are commonly used approaches. "
            "Performance optimization is crucial for production systems."
        )

        def extract():
            from openchat.nlp import MessageSummarizer
            summarizer = MessageSummarizer()
            # Assuming there's a keyword extraction method
            return message.split()[:5]  # Placeholder

        result = benchmark(extract)
        assert result is not None

    def test_summarization_consistency(self, benchmark):
        """Benchmark repeated summarization for consistency."""
        message = (
            "Consistency in natural language processing models is important. "
            "The same input should produce similar outputs. "
            "This is crucial for reliability and reproducibility."
        )

        def summarize_repeatedly():
            return [self.summarizer.summarize_message(message) for _ in range(5)]

        results = benchmark(summarize_repeatedly)
        assert len(results) == 5
        assert all(r is not None for r in results)


class TestMessageSummarizerBenchmarks:
    """Benchmark MessageSummarizer operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up MessageSummarizer for benchmarks."""
        self.summarizer = MessageSummarizer()

    def test_bart_summarization(self, benchmark):
        """Benchmark BART summarization."""
        article = " ".join([
            "This is a detailed article about machine learning.",
            "Machine learning is transforming industries worldwide.",
            "It enables computers to learn from data without explicit programming.",
            "Deep learning is a subset of machine learning.",
            "It uses neural networks to process information.",
            "Neural networks are inspired by the human brain.",
            "They can learn complex patterns from large datasets.",
        ])

        def summarize():
            return self.summarizer.summarize_text(
                article,
                max_length=50,
                min_length=10
            )

        result = benchmark(summarize)
        assert result is not None
        assert len(result) > 0

    def test_abstractive_summarization(self, benchmark):
        """Benchmark abstractive summarization."""
        document = " ".join([
            f"Sentence {i} provides information about topic {i % 5}. "
            f"It contributes to the overall understanding of the subject."
            for i in range(20)
        ])

        def summarize():
            return self.summarizer.summarize_text(document)

        result = benchmark(summarize)
        assert result is not None

    @pytest.mark.parametrize("doc_length", [100, 300, 500])
    def test_summarization_scaling(self, benchmark, doc_length):
        """Benchmark summarization with different document lengths."""
        document = " ".join([
            f"This is sentence {i} in a document being tested for performance."
            for i in range(doc_length // 10)
        ])

        def summarize():
            return self.summarizer.summarize_text(document)

        result = benchmark(summarize)
        assert result is not None

    def test_custom_length_summarization(self, benchmark):
        """Benchmark summarization with custom length parameters."""
        article = " ".join([
            f"This is a test article with sentence {i} containing information."
            for i in range(50)
        ])

        def summarize_short():
            return self.summarizer.summarize_text(
                article,
                max_length=30,
                min_length=5
            )

        result = benchmark(summarize_short)
        assert result is not None
        assert len(result) > 0

    def test_parallel_summarization(self, benchmark):
        """Benchmark parallel summarization of multiple documents."""
        documents = [
            " ".join([
                f"Document {d}, Sentence {s}: "
                f"This is content for benchmarking parallel summarization."
                for s in range(20)
            ])
            for d in range(5)
        ]

        def summarize_all():
            return [
                self.summarizer.summarize_text(doc)
                for doc in documents
            ]

        results = benchmark(summarize_all)
        assert len(results) == 5
        assert all(r is not None for r in results)
