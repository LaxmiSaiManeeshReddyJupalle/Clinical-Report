"""
Test Suite for Vector Store Module

Tests ChromaDB integration and document ingestion pipeline.

Run with: pytest tests/test_vector_store.py -v
"""

import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.vector_store import (
    ClinicalVectorStore,
    DocumentChunk,
    RetrievalResult,
    DocumentIngestionPipeline,
    create_vector_store,
    create_ingestion_pipeline
)


class TestClinicalVectorStore:
    """Test cases for ClinicalVectorStore class."""

    @pytest.fixture
    def vector_store(self):
        """Create an in-memory vector store for testing."""
        return ClinicalVectorStore(persist_dir=None, collection_name="test_collection")

    @pytest.fixture
    def sample_chunks(self):
        """Create sample document chunks."""
        return [
            DocumentChunk(
                text="Patient presents with symptoms of major depressive disorder.",
                metadata={"source": "admission.txt", "chunk_index": 0},
                doc_id="test_doc_1_0"
            ),
            DocumentChunk(
                text="Current medications include Sertraline 50mg daily.",
                metadata={"source": "admission.txt", "chunk_index": 1},
                doc_id="test_doc_1_1"
            ),
            DocumentChunk(
                text="Patient reports improved mood and sleep patterns.",
                metadata={"source": "progress.txt", "chunk_index": 0},
                doc_id="test_doc_2_0"
            ),
        ]

    def test_store_initialization(self, vector_store):
        """Test vector store initializes correctly."""
        assert vector_store is not None
        assert vector_store.collection_name == "test_collection"

    def test_add_documents(self, vector_store, sample_chunks):
        """Test adding documents to the store."""
        added = vector_store.add_documents(sample_chunks)
        assert added == 3

        stats = vector_store.get_collection_stats()
        assert stats['count'] == 3

    def test_add_empty_documents(self, vector_store):
        """Test adding empty document list."""
        added = vector_store.add_documents([])
        assert added == 0

    def test_query(self, vector_store, sample_chunks):
        """Test querying the vector store."""
        vector_store.add_documents(sample_chunks)

        results = vector_store.query("depression symptoms", n_results=2)

        assert 'documents' in results
        assert 'distances' in results
        assert len(results['documents'][0]) <= 2

    def test_search(self, vector_store, sample_chunks):
        """Test search with structured results."""
        vector_store.add_documents(sample_chunks)

        results = vector_store.search("medication sertraline", n_results=2)

        assert len(results) > 0
        assert isinstance(results[0], RetrievalResult)
        assert results[0].relevance_score > 0

    def test_query_with_filter(self, vector_store, sample_chunks):
        """Test querying with metadata filter."""
        vector_store.add_documents(sample_chunks)

        results = vector_store.query(
            "patient symptoms",
            n_results=5,
            filter_metadata={"source": "admission.txt"}
        )

        # All results should be from admission.txt
        for meta in results['metadatas'][0]:
            assert meta['source'] == "admission.txt"

    def test_delete_by_metadata(self, vector_store, sample_chunks):
        """Test deleting documents by metadata."""
        vector_store.add_documents(sample_chunks)

        # Delete admission documents
        vector_store.delete_by_metadata({"source": "admission.txt"})

        stats = vector_store.get_collection_stats()
        # Should only have 1 document left (progress.txt)
        assert stats['count'] == 1

    def test_clear(self, vector_store, sample_chunks):
        """Test clearing the vector store."""
        vector_store.add_documents(sample_chunks)
        assert vector_store.get_collection_stats()['count'] == 3

        vector_store.clear()
        assert vector_store.get_collection_stats()['count'] == 0

    def test_collection_stats(self, vector_store, sample_chunks):
        """Test getting collection statistics."""
        vector_store.add_documents(sample_chunks)

        stats = vector_store.get_collection_stats()

        assert 'name' in stats
        assert 'count' in stats
        assert stats['count'] == 3


class TestRetrievalResult:
    """Test cases for RetrievalResult dataclass."""

    def test_relevance_score_calculation(self):
        """Test relevance score calculation from distance."""
        result = RetrievalResult(
            text="test",
            metadata={},
            distance=0.0,
            doc_id="test"
        )
        # Distance 0 should give high relevance
        assert result.relevance_score == 1.0

        result2 = RetrievalResult(
            text="test",
            metadata={},
            distance=1.0,
            doc_id="test"
        )
        # Distance 1 should give relevance 0.5
        assert result2.relevance_score == 0.5


class TestDocumentIngestionPipeline:
    """Test cases for DocumentIngestionPipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create ingestion pipeline with in-memory store."""
        vector_store = ClinicalVectorStore(persist_dir=None, collection_name="test_ingestion")
        return DocumentIngestionPipeline(
            vector_store=vector_store,
            scrub_pii=True,
            chunk_size=500,
            chunk_overlap=50
        )

    @pytest.fixture
    def mock_data_path(self):
        """Get path to mock data."""
        return Path(__file__).parent.parent / "mock_data"

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes correctly."""
        assert pipeline is not None
        assert pipeline.scrub_pii is True

    def test_ingest_single_document(self, pipeline, mock_data_path):
        """Test ingesting a single document."""
        txt_files = list(mock_data_path.glob("**/*.txt"))

        if not txt_files:
            pytest.skip("No mock documents found")

        result = pipeline.ingest_document(txt_files[0])

        assert result['success']
        assert result['chunks_added'] > 0

    def test_ingest_with_pii_scrubbing(self, pipeline, mock_data_path):
        """Test that PII is scrubbed during ingestion."""
        admission_files = list(mock_data_path.glob("**/admission_summary.txt"))

        if not admission_files:
            pytest.skip("No admission summaries found")

        result = pipeline.ingest_document(admission_files[0])
        assert result['success']

        # Query the vector store and check for PII markers
        search_results = pipeline.vector_store.search("patient information", n_results=5)

        # At least some results should have PHI markers from scrubbing
        all_text = " ".join(r.text for r in search_results)
        # SSN should be redacted (shouldn't have XXX-XX-XXXX pattern)
        import re
        ssn_pattern = r'\d{3}-\d{2}-\d{4}'
        # The scrubbed text should not contain raw SSNs
        assert not re.search(ssn_pattern, all_text), "SSN should be scrubbed"

    def test_ingest_patient_documents(self, pipeline, mock_data_path):
        """Test ingesting all documents for a patient."""
        # Find a patient folder
        patient_dirs = list(mock_data_path.glob("**/*/"))
        patient_dirs = [d for d in patient_dirs if d.is_dir() and not d.name.startswith('FY')]

        if not patient_dirs:
            pytest.skip("No patient folders found")

        patient_dir = patient_dirs[0]
        files = list(patient_dir.glob("*.txt"))

        result = pipeline.ingest_patient_documents(
            files,
            patient_id="test_patient",
            year="FY 25"
        )

        assert result['successful'] == len(files)
        assert result['total_chunks'] > 0

    def test_ingest_mock_data(self, mock_data_path):
        """Test ingesting all mock data."""
        # Use a fresh vector store
        vector_store = ClinicalVectorStore(persist_dir=None, collection_name="test_full_ingest")
        pipeline = DocumentIngestionPipeline(
            vector_store=vector_store,
            scrub_pii=False,  # Faster without scrubbing for this test
            chunk_size=1000
        )

        result = pipeline.ingest_mock_data(mock_data_path)

        assert result['success']
        assert result['patients'] > 0
        assert result['documents'] > 0
        assert result['chunks'] > 0

        # Verify data is queryable
        stats = vector_store.get_collection_stats()
        assert stats['count'] == result['chunks']


class TestPersistentVectorStore:
    """Test persistent vector store functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for persistent storage."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    def test_persistent_store(self, temp_dir):
        """Test that data persists across store instances."""
        # Create store and add data
        store1 = ClinicalVectorStore(
            persist_dir=temp_dir,
            collection_name="persist_test"
        )

        chunks = [
            DocumentChunk(
                text="Persistent test document",
                metadata={"test": True},
                doc_id="persist_1"
            )
        ]
        store1.add_documents(chunks)
        count1 = store1.get_collection_stats()['count']

        # Create new store instance with same path
        store2 = ClinicalVectorStore(
            persist_dir=temp_dir,
            collection_name="persist_test"
        )

        # Data should persist
        count2 = store2.get_collection_stats()['count']
        assert count2 == count1


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_vector_store(self):
        """Test create_vector_store factory."""
        store = create_vector_store(persist_dir=None, collection_name="factory_test")
        assert store is not None

    def test_create_ingestion_pipeline(self):
        """Test create_ingestion_pipeline factory."""
        pipeline = create_ingestion_pipeline(persist_dir=None, scrub_pii=False)
        assert pipeline is not None
        assert pipeline.scrub_pii is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
