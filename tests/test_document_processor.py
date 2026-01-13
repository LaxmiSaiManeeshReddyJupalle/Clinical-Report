"""
Test Suite for Document Processor Module

Tests text extraction and chunking capabilities.

Run with: pytest tests/test_document_processor.py -v
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.document_processor import (
    DocumentProcessor,
    TextExtractor,
    TextChunker,
    DocumentType,
    DocumentChunk,
    ProcessedDocument,
    create_document_processor
)


class TestTextExtractor:
    """Test cases for TextExtractor class."""

    @pytest.fixture
    def extractor(self):
        return TextExtractor()

    def test_detect_pdf_type(self, extractor):
        """Test PDF type detection."""
        assert extractor.detect_type("document.pdf") == DocumentType.PDF
        assert extractor.detect_type("document.PDF") == DocumentType.PDF

    def test_detect_docx_type(self, extractor):
        """Test DOCX type detection."""
        assert extractor.detect_type("document.docx") == DocumentType.DOCX

    def test_detect_txt_type(self, extractor):
        """Test TXT type detection."""
        assert extractor.detect_type("document.txt") == DocumentType.TXT

    def test_detect_unknown_type(self, extractor):
        """Test unknown type detection."""
        assert extractor.detect_type("document.xyz") == DocumentType.UNKNOWN

    def test_extract_txt(self, extractor):
        """Test text extraction from TXT content."""
        content = b"This is a test document.\nWith multiple lines."
        text, pages = extractor.extract_from_txt(content)

        assert "This is a test document" in text
        assert "multiple lines" in text
        assert pages == 1

    def test_extract_txt_unicode(self, extractor):
        """Test text extraction with unicode content."""
        content = "Hello, 世界! Héllo wörld.".encode('utf-8')
        text, pages = extractor.extract_from_txt(content)

        assert "Hello" in text
        assert "世界" in text


class TestTextChunker:
    """Test cases for TextChunker class."""

    @pytest.fixture
    def chunker(self):
        return TextChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=20)

    def test_chunker_initialization(self, chunker):
        """Test chunker initializes correctly."""
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 20
        assert chunker.min_chunk_size == 20

    def test_chunk_empty_text(self, chunker):
        """Test chunking empty text returns empty list."""
        chunks = chunker.chunk_by_size("")
        assert chunks == []

    def test_chunk_small_text(self, chunker):
        """Test chunking text smaller than chunk size."""
        text = "This is a short text that fits in one chunk."
        chunks = chunker.chunk_by_size(text)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_chunk_large_text(self, chunker):
        """Test chunking text larger than chunk size."""
        # Create text that's definitely longer than chunk_size
        text = "This is a sentence. " * 20  # ~400 chars
        chunks = chunker.chunk_by_size(text)

        assert len(chunks) > 1
        # Verify chunks have overlap
        for i in range(1, len(chunks)):
            assert chunks[i].start_char < chunks[i-1].end_char

    def test_chunk_metadata(self, chunker):
        """Test that chunks include metadata."""
        text = "Test text for metadata verification."
        metadata = {"source": "test_file.txt", "patient_id": "test123"}
        chunks = chunker.chunk_by_size(text, metadata)

        assert len(chunks) == 1
        assert chunks[0].metadata['source'] == "test_file.txt"
        assert chunks[0].metadata['chunk_index'] == 0

    def test_chunk_by_paragraph(self, chunker):
        """Test paragraph-based chunking."""
        text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph."
        chunks = chunker.chunk_by_paragraph(text)

        assert len(chunks) >= 1
        # All original content should be present
        all_text = " ".join(c.text for c in chunks)
        assert "First paragraph" in all_text
        assert "Second paragraph" in all_text


class TestDocumentProcessor:
    """Test cases for DocumentProcessor class."""

    @pytest.fixture
    def processor(self):
        return DocumentProcessor(chunk_size=500, chunk_overlap=100)

    @pytest.fixture
    def mock_data_path(self):
        return Path(__file__).parent.parent / "mock_data"

    def test_processor_initialization(self, processor):
        """Test processor initializes correctly."""
        assert processor is not None
        assert processor.chunking_strategy == "size"

    def test_process_txt_file(self, processor, mock_data_path):
        """Test processing a TXT file from mock data."""
        txt_files = list(mock_data_path.glob("**/*.txt"))

        if not txt_files:
            pytest.skip("No mock TXT files found")

        result = processor.process_file(txt_files[0])

        assert result.success
        assert result.document_type == DocumentType.TXT
        assert result.total_chars > 0
        assert len(result.chunks) > 0

    def test_process_multiple_files(self, processor, mock_data_path):
        """Test processing multiple files."""
        txt_files = list(mock_data_path.glob("**/*.txt"))[:5]

        if not txt_files:
            pytest.skip("No mock TXT files found")

        results = processor.process_multiple(txt_files)

        assert len(results) == len(txt_files)
        assert all(r.success for r in results)

    def test_process_with_metadata(self, processor, mock_data_path):
        """Test processing with additional metadata."""
        txt_files = list(mock_data_path.glob("**/*.txt"))

        if not txt_files:
            pytest.skip("No mock TXT files found")

        metadata = {"year": "FY 25", "category": "clinical"}
        result = processor.process_file(txt_files[0], additional_metadata=metadata)

        assert result.success
        assert result.metadata.get('year') == "FY 25"
        assert result.metadata.get('category') == "clinical"

    def test_process_nonexistent_file(self, processor):
        """Test processing nonexistent file returns error."""
        result = processor.process_file("/nonexistent/path/file.txt")

        assert not result.success
        assert result.error_message is not None


class TestDocumentChunk:
    """Test cases for DocumentChunk dataclass."""

    def test_chunk_char_count(self):
        """Test chunk character count property."""
        chunk = DocumentChunk(
            text="Hello world",
            metadata={},
            chunk_index=0,
            start_char=0,
            end_char=11
        )

        assert chunk.char_count == 11


class TestProcessedDocument:
    """Test cases for ProcessedDocument dataclass."""

    def test_processed_document_creation(self):
        """Test ProcessedDocument creation."""
        doc = ProcessedDocument(
            source_path="/test/path.txt",
            document_type=DocumentType.TXT,
            total_chars=100,
            total_pages=1,
            raw_text="Test content",
            chunks=[],
            metadata={"source": "test"},
            success=True
        )

        assert doc.source_path == "/test/path.txt"
        assert doc.success
        assert doc.error_message is None


class TestFactoryFunction:
    """Test factory function."""

    def test_create_document_processor_default(self):
        """Test default processor creation."""
        processor = create_document_processor()

        assert processor is not None
        assert processor.chunker.chunk_size == 1000

    def test_create_document_processor_custom(self):
        """Test custom processor creation."""
        processor = create_document_processor(
            chunk_size=500,
            chunk_overlap=50,
            strategy="paragraph"
        )

        assert processor.chunker.chunk_size == 500
        assert processor.chunking_strategy == "paragraph"


class TestMockDocumentProcessing:
    """Test processing actual mock documents."""

    @pytest.fixture
    def mock_data_path(self):
        return Path(__file__).parent.parent / "mock_data"

    @pytest.fixture
    def processor(self):
        return DocumentProcessor(chunk_size=800, chunk_overlap=100)

    def test_mock_data_exists(self, mock_data_path):
        """Verify mock data exists."""
        assert mock_data_path.exists()

    def test_process_all_mock_documents(self, mock_data_path, processor):
        """Process all mock documents and verify success."""
        all_docs = list(mock_data_path.glob("**/*.txt"))

        if not all_docs:
            pytest.skip("No mock documents found")

        results = processor.process_multiple(all_docs)

        # All documents should process successfully
        successful = sum(1 for r in results if r.success)
        assert successful == len(all_docs), f"Expected all {len(all_docs)} to succeed, got {successful}"

    def test_chunk_coverage(self, mock_data_path, processor):
        """Verify chunks cover all document content."""
        txt_files = list(mock_data_path.glob("**/*.txt"))

        if not txt_files:
            pytest.skip("No mock documents found")

        result = processor.process_file(txt_files[0])

        # Verify chunks are created
        assert len(result.chunks) > 0

        # Verify chunks cover reasonable portion of document
        total_chunk_chars = sum(c.char_count for c in result.chunks)
        # Allow for some overhead due to overlap
        assert total_chunk_chars >= result.total_chars * 0.8

    def test_clinical_content_preserved(self, mock_data_path, processor):
        """Verify clinical content is preserved in chunks."""
        admission_files = list(mock_data_path.glob("**/admission_summary.txt"))

        if not admission_files:
            pytest.skip("No admission summaries found")

        result = processor.process_file(admission_files[0])

        # Combine all chunk text
        all_chunk_text = " ".join(c.text for c in result.chunks)

        # Key clinical terms should be preserved
        assert "ADMISSION" in all_chunk_text.upper()
        assert "PATIENT" in all_chunk_text.upper()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
