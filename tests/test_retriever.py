"""
Test Suite for RAG Retrieval System

Tests retrieval, context building, and report generation.

Run with: pytest tests/test_retriever.py -v
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.vector_store import (
    ClinicalVectorStore,
    DocumentChunk,
    DocumentIngestionPipeline
)
from src.rag.retriever import (
    ClinicalRetriever,
    ReportGenerator,
    PromptBuilder,
    RetrievalConfig,
    GenerationConfig,
    RAGContext,
    GeneratedReport,
    ReportType,
    create_rag_system
)


class TestClinicalRetriever:
    """Test cases for ClinicalRetriever class."""

    @pytest.fixture
    def populated_store(self):
        """Create vector store with sample clinical data."""
        store = ClinicalVectorStore(persist_dir=None, collection_name="test_retriever")

        chunks = [
            DocumentChunk(
                text="Patient admitted with major depressive disorder. Reports persistent sad mood, anhedonia, and sleep disturbance for past 3 weeks.",
                metadata={"source": "admission.txt", "patient_id": "patient_001", "chunk_index": 0},
                doc_id="doc1_0"
            ),
            DocumentChunk(
                text="Current medications: Sertraline 50mg daily, Trazodone 50mg at bedtime for sleep.",
                metadata={"source": "admission.txt", "patient_id": "patient_001", "chunk_index": 1},
                doc_id="doc1_1"
            ),
            DocumentChunk(
                text="Day 3 progress note: Patient reports slight improvement in mood. Sleep improving with Trazodone. Participating in group therapy.",
                metadata={"source": "progress_day3.txt", "patient_id": "patient_001", "chunk_index": 0},
                doc_id="doc2_0"
            ),
            DocumentChunk(
                text="Patient with anxiety disorder. Presenting with panic attacks, difficulty concentrating, and social avoidance.",
                metadata={"source": "admission.txt", "patient_id": "patient_002", "chunk_index": 0},
                doc_id="doc3_0"
            ),
            DocumentChunk(
                text="Mental status examination: Alert and oriented x4. Mood depressed. Affect constricted. No suicidal ideation.",
                metadata={"source": "assessment.txt", "patient_id": "patient_001", "chunk_index": 0},
                doc_id="doc4_0"
            ),
        ]

        store.add_documents(chunks)
        return store

    @pytest.fixture
    def retriever(self, populated_store):
        """Create retriever with populated store."""
        config = RetrievalConfig(n_results=5, relevance_threshold=0.0)
        return ClinicalRetriever(populated_store, config)

    def test_retriever_initialization(self, retriever):
        """Test retriever initializes correctly."""
        assert retriever is not None
        assert retriever.config.n_results == 5

    def test_basic_retrieval(self, retriever):
        """Test basic document retrieval."""
        results = retriever.retrieve("depression symptoms")

        assert len(results) > 0
        # Should retrieve depression-related content
        all_text = " ".join(r.text.lower() for r in results)
        assert "depress" in all_text

    def test_retrieve_for_patient(self, retriever):
        """Test patient-specific retrieval."""
        results = retriever.retrieve_for_patient(
            query="medications treatment",
            patient_id="patient_001"
        )

        assert len(results) > 0
        # All results should be for patient_001
        for result in results:
            assert result.metadata.get('patient_id') == 'patient_001'

    def test_retrieve_with_threshold(self, populated_store):
        """Test retrieval with relevance threshold."""
        # High threshold should filter out less relevant results
        config = RetrievalConfig(n_results=10, relevance_threshold=0.5)
        retriever = ClinicalRetriever(populated_store, config)

        results = retriever.retrieve("very specific unique query xyz123")
        # May return fewer or no results due to high threshold
        assert len(results) <= 10

    def test_build_context(self, retriever):
        """Test context building from results."""
        results = retriever.retrieve("patient symptoms")
        context = retriever.build_context("patient symptoms", results)

        assert isinstance(context, RAGContext)
        assert len(context.context_text) > 0
        assert context.total_chunks == len(results)

    def test_context_max_chars(self, retriever):
        """Test context respects max character limit."""
        results = retriever.retrieve("patient")
        context = retriever.build_context("patient", results, max_chars=200)

        assert len(context.context_text) <= 200 + 100  # Some overhead for headers

    def test_context_includes_sources(self, retriever):
        """Test context includes source metadata."""
        results = retriever.retrieve("patient")
        context = retriever.build_context("patient", results)

        # Sources should be tracked
        assert 'sources' in context.metadata
        assert len(context.metadata['sources']) > 0


class TestPromptBuilder:
    """Test cases for PromptBuilder class."""

    @pytest.fixture
    def sample_context(self):
        """Create sample RAG context."""
        return RAGContext(
            query="patient summary",
            retrieved_chunks=[],
            total_chunks=3,
            context_text="Sample clinical content here.",
            metadata={'sources': ['admission.txt']}
        )

    def test_build_full_summary_prompt(self, sample_context):
        """Test building full summary prompt."""
        prompts = PromptBuilder.build_prompt(
            report_type=ReportType.FULL_SUMMARY,
            context=sample_context
        )

        assert 'system' in prompts
        assert 'user' in prompts
        assert "comprehensive" in prompts['system'].lower()
        assert sample_context.context_text in prompts['user']

    def test_build_progress_summary_prompt(self, sample_context):
        """Test building progress summary prompt."""
        prompts = PromptBuilder.build_prompt(
            report_type=ReportType.PROGRESS_SUMMARY,
            context=sample_context
        )

        assert "progress" in prompts['system'].lower()

    def test_build_medication_review_prompt(self, sample_context):
        """Test building medication review prompt."""
        prompts = PromptBuilder.build_prompt(
            report_type=ReportType.MEDICATION_REVIEW,
            context=sample_context
        )

        assert "medication" in prompts['system'].lower()

    def test_custom_instruction(self, sample_context):
        """Test prompt with custom instruction."""
        custom = "focus on sleep patterns and interventions"
        prompts = PromptBuilder.build_prompt(
            report_type=ReportType.FULL_SUMMARY,
            context=sample_context,
            custom_instruction=custom
        )

        assert custom in prompts['user']


class TestReportGenerator:
    """Test cases for ReportGenerator class."""

    @pytest.fixture
    def populated_store(self):
        """Create populated vector store."""
        store = ClinicalVectorStore(persist_dir=None, collection_name="test_generator")

        chunks = [
            DocumentChunk(
                text="Patient admitted with major depressive disorder, recurrent, moderate severity. History of 2 previous episodes.",
                metadata={"source": "admission.txt", "patient_id": "test_patient", "chunk_index": 0},
                doc_id="gen_doc1"
            ),
            DocumentChunk(
                text="Medications on admission: Sertraline 100mg daily (increased from 50mg 1 week ago), Trazodone 50mg qhs.",
                metadata={"source": "admission.txt", "patient_id": "test_patient", "chunk_index": 1},
                doc_id="gen_doc2"
            ),
            DocumentChunk(
                text="Progress note day 5: Patient showing improvement in mood. PHQ-9 decreased from 18 to 12. Sleep normalized. Engaging well in groups.",
                metadata={"source": "progress.txt", "patient_id": "test_patient", "chunk_index": 0},
                doc_id="gen_doc3"
            ),
        ]

        store.add_documents(chunks)
        return store

    @pytest.fixture
    def generator(self, populated_store):
        """Create report generator without LLM."""
        retriever = ClinicalRetriever(populated_store)
        return ReportGenerator(retriever, llm_client=None)

    def test_generator_initialization(self, generator):
        """Test generator initializes correctly."""
        assert generator is not None
        assert generator.llm_client is None

    def test_generate_report_without_llm(self, generator):
        """Test report generation without LLM returns structured content."""
        report = generator.generate_report(
            query="patient depression summary",
            report_type=ReportType.FULL_SUMMARY
        )

        assert isinstance(report, GeneratedReport)
        assert report.report_type == ReportType.FULL_SUMMARY
        assert len(report.content) > 0
        # Should now return structured report with actual content
        assert "Full Summary" in report.content or "admission" in report.content.lower()

    def test_generate_report_with_patient_filter(self, generator):
        """Test report generation for specific patient."""
        report = generator.generate_report(
            query="treatment progress",
            report_type=ReportType.PROGRESS_SUMMARY,
            patient_id="test_patient"
        )

        assert report.context_used > 0
        assert len(report.sources) > 0

    def test_generate_patient_summary(self, generator):
        """Test patient summary generation."""
        report = generator.generate_patient_summary(
            patient_id="test_patient",
            report_type=ReportType.FULL_SUMMARY
        )

        assert isinstance(report, GeneratedReport)
        assert report.context_used > 0

    def test_report_metadata(self, generator):
        """Test report includes metadata."""
        report = generator.generate_report(
            query="patient information",
            report_type=ReportType.FULL_SUMMARY
        )

        assert 'query' in report.metadata
        assert 'total_retrieved' in report.metadata

    def test_empty_retrieval_handling(self, populated_store):
        """Test handling when no documents are retrieved."""
        retriever = ClinicalRetriever(
            populated_store,
            RetrievalConfig(relevance_threshold=0.99)  # Very high threshold
        )
        generator = ReportGenerator(retriever)

        report = generator.generate_report(
            query="completely unrelated xyz123",
            report_type=ReportType.FULL_SUMMARY
        )

        # Should handle gracefully
        assert report.context_used == 0
        assert "no relevant documents" in report.content.lower() or "unable" in report.content.lower()


class TestReportTypes:
    """Test different report types."""

    def test_all_report_types_have_prompts(self):
        """Test all report types have system prompts."""
        for report_type in ReportType:
            assert report_type in PromptBuilder.SYSTEM_PROMPTS or \
                   report_type == ReportType.FULL_SUMMARY


class TestFactoryFunction:
    """Test factory function."""

    def test_create_rag_system(self):
        """Test create_rag_system factory."""
        store = ClinicalVectorStore(persist_dir=None, collection_name="factory_test")
        generator = create_rag_system(store, llm_client=None)

        assert isinstance(generator, ReportGenerator)


class TestIntegrationWithMockData:
    """Integration tests with mock data."""

    @pytest.fixture
    def mock_data_path(self):
        return Path(__file__).parent.parent / "mock_data"

    @pytest.fixture
    def ingested_store(self, mock_data_path):
        """Create store with ingested mock data."""
        if not mock_data_path.exists():
            pytest.skip("Mock data not found")

        store = ClinicalVectorStore(persist_dir=None, collection_name="integration_test")
        pipeline = DocumentIngestionPipeline(
            vector_store=store,
            scrub_pii=False,  # Faster for tests
            chunk_size=500
        )

        # Ingest just a few documents for speed
        txt_files = list(mock_data_path.glob("**/admission_summary.txt"))[:3]
        for f in txt_files:
            pipeline.ingest_document(f)

        return store

    def test_full_rag_pipeline(self, ingested_store):
        """Test complete RAG pipeline with mock data."""
        generator = create_rag_system(ingested_store)

        report = generator.generate_report(
            query="patient admission summary symptoms",
            report_type=ReportType.FULL_SUMMARY
        )

        assert report.context_used > 0
        assert len(report.sources) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
