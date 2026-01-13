"""
RAG Retrieval System for UIC ATU Clinical Report Generator

Provides retrieval-augmented generation for clinical report synthesis.
Combines vector search with LLM-based response generation.

SECURITY: Handles PHI in retrieved context. All prompts and responses
should be handled securely and not logged.
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.rag.vector_store import ClinicalVectorStore, RetrievalResult

# Configure logging (no PHI)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of clinical reports that can be generated."""
    FULL_SUMMARY = "full_summary"
    PROGRESS_SUMMARY = "progress_summary"
    MEDICATION_REVIEW = "medication_review"
    DISCHARGE_SUMMARY = "discharge_summary"
    ASSESSMENT_SUMMARY = "assessment_summary"


@dataclass
class RetrievalConfig:
    """Configuration for retrieval operations."""
    n_results: int = 5  # More chunks for comprehensive reports
    relevance_threshold: float = 0.3  # Lower threshold to include more context
    max_context_chars: int = 4000  # More context for detailed LLM generation
    include_metadata: bool = True


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 2000
    temperature: float = 0.3
    model: str = "gpt-4"


@dataclass
class RAGContext:
    """Context assembled for RAG generation."""
    query: str
    retrieved_chunks: List[RetrievalResult]
    total_chunks: int
    context_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedReport:
    """Result of report generation."""
    report_type: ReportType
    content: str
    context_used: int  # Number of chunks used
    sources: List[str]  # Source documents
    metadata: Dict[str, Any]


class ClinicalRetriever:
    """
    Retrieval component for clinical documents.

    Retrieves relevant document chunks based on semantic similarity.

    SECURITY: Retrieved content contains PHI - handle securely.
    """

    def __init__(
        self,
        vector_store: ClinicalVectorStore,
        config: Optional[RetrievalConfig] = None
    ):
        """
        Initialize retriever.

        Args:
            vector_store: Vector store for document retrieval
            config: Retrieval configuration
        """
        self.vector_store = vector_store
        self.config = config or RetrievalConfig()

    def retrieve(
        self,
        query: str,
        n_results: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: Search query
            n_results: Override number of results
            filter_metadata: Optional metadata filter

        Returns:
            List of RetrievalResult objects
        """
        n = n_results or self.config.n_results

        results = self.vector_store.search(
            query_text=query,
            n_results=n,
            filter_metadata=filter_metadata
        )

        # Filter by relevance threshold
        filtered = [
            r for r in results
            if r.relevance_score >= self.config.relevance_threshold
        ]

        logger.info(f"Retrieved {len(filtered)} relevant chunks (threshold: {self.config.relevance_threshold})")
        return filtered

    def retrieve_for_patient(
        self,
        query: str,
        patient_id: str,
        n_results: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve documents for a specific patient.

        Args:
            query: Search query
            patient_id: Patient identifier
            n_results: Override number of results

        Returns:
            List of RetrievalResult objects for the patient
        """
        return self.retrieve(
            query=query,
            n_results=n_results,
            filter_metadata={"patient_id": patient_id}
        )

    def build_context(
        self,
        query: str,
        results: List[RetrievalResult],
        max_chars: Optional[int] = None
    ) -> RAGContext:
        """
        Build context string from retrieval results.

        Args:
            query: Original query
            results: Retrieved results
            max_chars: Maximum context characters

        Returns:
            RAGContext with assembled context
        """
        max_chars = max_chars or self.config.max_context_chars

        context_parts = []
        current_chars = 0
        used_chunks = []
        sources = set()

        for result in results:
            chunk_text = result.text
            chunk_chars = len(chunk_text)

            # Check if adding this chunk would exceed limit
            if current_chars + chunk_chars > max_chars:
                break

            # Add chunk to context
            if self.config.include_metadata:
                source = result.metadata.get('source', 'Unknown')
                sources.add(source)
                chunk_header = f"[Source: {source}]\n"
                context_parts.append(chunk_header + chunk_text)
            else:
                context_parts.append(chunk_text)

            current_chars += chunk_chars
            used_chunks.append(result)

        context_text = "\n\n---\n\n".join(context_parts)

        return RAGContext(
            query=query,
            retrieved_chunks=used_chunks,
            total_chunks=len(results),
            context_text=context_text,
            metadata={
                'sources': list(sources),
                'chars_used': current_chars
            }
        )


class PromptBuilder:
    """
    Builds prompts for clinical report generation.

    Creates structured prompts based on report type and context.
    """

    # Comprehensive prompts for detailed clinical reports
    SYSTEM_PROMPTS = {
        ReportType.FULL_SUMMARY: """You are a clinical documentation specialist creating comprehensive patient summaries.
Generate a detailed clinical summary that includes:
- Patient presentation and chief complaint
- Relevant history
- Assessment findings (organized chronologically by date when available)
- Treatment plan and interventions (medications with dosages, therapy, group participation)
- Progress and outcomes
- Recommendations for continued care

Use professional clinical language. Only include information explicitly stated in the provided documentation.
Organize information clearly with headers and bullet points where appropriate.""",

        ReportType.PROGRESS_SUMMARY: """You are a clinical documentation specialist summarizing patient progress.
Create a comprehensive progress summary including:
- Overall treatment trajectory
- Symptom changes over time (organized by date)
- Response to treatment interventions
- Current clinical status
- Areas of improvement and ongoing concerns

Present information in chronological order using clinical language.""",

        ReportType.MEDICATION_REVIEW: """You are a clinical pharmacist reviewing patient medications.
Create a detailed medication review including:
- Current medications (name, dosage, frequency, route)
- Medication changes during treatment
- Therapeutic effectiveness
- Side effects or adverse reactions
- Adherence/compliance notes
- Recommendations

Only include medications explicitly documented in the records.""",

        ReportType.DISCHARGE_SUMMARY: """You are a clinical documentation specialist creating a discharge summary.
Include:
- Reason for admission
- Hospital course (day-by-day if available)
- Condition at discharge
- Discharge medications with dosages
- Follow-up appointments and instructions
- Safety plan and crisis resources
- Recommendations for outpatient care

Use professional clinical language.""",

        ReportType.ASSESSMENT_SUMMARY: """You are a clinical documentation specialist creating an assessment summary.
Include:
- Mental status examination findings
- Diagnostic impressions
- Risk assessment (safety, harm to self/others)
- Functional status
- Treatment recommendations
- Limitations and areas requiring further assessment

Note any limitations in the available documentation."""
    }

    USER_PROMPT_TEMPLATE = """Based on the following clinical documentation, generate a comprehensive {report_type}:

{context}

Provide a thorough and well-organized summary. Include specific dates, dosages, and clinical details where available."""

    @classmethod
    def build_prompt(
        cls,
        report_type: ReportType,
        context: RAGContext,
        custom_instruction: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Build prompt for report generation.

        Args:
            report_type: Type of report to generate
            context: RAG context with retrieved documents
            custom_instruction: Optional custom instruction

        Returns:
            Dictionary with 'system' and 'user' prompts
        """
        system_prompt = cls.SYSTEM_PROMPTS.get(
            report_type,
            cls.SYSTEM_PROMPTS[ReportType.FULL_SUMMARY]
        )

        instruction = custom_instruction or f"generate a {report_type.value.replace('_', ' ')}"

        user_prompt = cls.USER_PROMPT_TEMPLATE.format(
            instruction=instruction,
            context=context.context_text,
            report_type=report_type.value.replace('_', ' ')
        )

        return {
            'system': system_prompt,
            'user': user_prompt
        }


class ReportGenerator:
    """
    Generates clinical reports using RAG.

    Combines retrieval with LLM generation for report synthesis.

    SECURITY: Handles PHI throughout the generation process.
    """

    def __init__(
        self,
        retriever: ClinicalRetriever,
        llm_client: Optional[Any] = None,
        generation_config: Optional[GenerationConfig] = None
    ):
        """
        Initialize report generator.

        Args:
            retriever: Clinical retriever for document retrieval
            llm_client: Optional LLM client (OpenAI, Anthropic, etc.)
            generation_config: Generation configuration
        """
        self.retriever = retriever
        self.llm_client = llm_client
        self.config = generation_config or GenerationConfig()

    def _generate_with_llm(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Generate text using LLM.

        Supports OpenAI-style clients (including Ollama adapter).

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Generated text
        """
        if self.llm_client is None:
            # Return a placeholder response if no LLM client
            logger.warning("No LLM client configured - returning template response")
            return self._generate_template_response(user_prompt)

        # Implement LLM call for OpenAI-style interface
        try:
            # Check for OpenAI-compatible interface (works with Ollama adapter too)
            if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
                logger.info("Generating report with LLM")
                response = self.llm_client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
                content = response.choices[0].message.content
                logger.info(f"LLM generated {len(content)} characters")
                return content
            else:
                logger.warning("Unknown LLM client type - returning structured report")
                # Fall back to structured report instead of template
                return self._generate_template_response(user_prompt)

        except Exception as e:
            logger.error(f"LLM generation failed: {type(e).__name__}: {str(e)}")
            logger.info("Falling back to structured report")
            return self._generate_template_response(user_prompt)

    def _generate_structured_report(
        self,
        context: 'RAGContext',
        report_type: ReportType
    ) -> str:
        """
        Generate a structured report from retrieved content without LLM.

        Organizes the retrieved clinical content into a readable format.

        Args:
            context: RAG context with retrieved chunks
            report_type: Type of report being generated

        Returns:
            Formatted clinical report based on retrieved content
        """
        if not context.retrieved_chunks:
            return "No clinical documentation was retrieved for this patient."

        # Categorize chunks by document type
        admission_content = []
        progress_content = []
        discharge_content = []
        treatment_content = []
        other_content = []

        for chunk in context.retrieved_chunks:
            source = chunk.metadata.get('source', '').lower()
            text = chunk.text

            if 'admission' in source:
                admission_content.append((source, text))
            elif 'progress' in source:
                progress_content.append((source, text))
            elif 'discharge' in source:
                discharge_content.append((source, text))
            elif 'treatment' in source:
                treatment_content.append((source, text))
            else:
                other_content.append((source, text))

        # Build structured report
        report_parts = []

        # Header based on report type
        report_parts.append(f"## {report_type.value.replace('_', ' ').title()}\n")

        # Admission Information
        if admission_content:
            report_parts.append("### Admission Information\n")
            for source, text in admission_content:
                report_parts.append(f"**From: {source}**\n")
                report_parts.append(f"{text}\n")
                report_parts.append("---\n")

        # Treatment Plan
        if treatment_content:
            report_parts.append("### Treatment Plan\n")
            for source, text in treatment_content:
                report_parts.append(f"**From: {source}**\n")
                report_parts.append(f"{text}\n")
                report_parts.append("---\n")

        # Progress Notes
        if progress_content:
            report_parts.append("### Progress Notes\n")
            # Sort by source name to get chronological order
            progress_content.sort(key=lambda x: x[0])
            for source, text in progress_content:
                report_parts.append(f"**From: {source}**\n")
                report_parts.append(f"{text}\n")
                report_parts.append("---\n")

        # Discharge Information
        if discharge_content:
            report_parts.append("### Discharge Information\n")
            for source, text in discharge_content:
                report_parts.append(f"**From: {source}**\n")
                report_parts.append(f"{text}\n")
                report_parts.append("---\n")

        # Other Documents
        if other_content:
            report_parts.append("### Additional Documentation\n")
            for source, text in other_content:
                report_parts.append(f"**From: {source}**\n")
                report_parts.append(f"{text}\n")
                report_parts.append("---\n")

        # Add note about LLM integration
        report_parts.append("\n### Note\n")
        report_parts.append("*This report displays the retrieved clinical documentation in a structured format. ")
        report_parts.append("When an LLM is connected (e.g., via Ollama with a local model), ")
        report_parts.append("the content will be synthesized into a cohesive clinical narrative.*\n")

        return "\n".join(report_parts)

    def _generate_template_response(self, prompt: str) -> str:
        """
        Generate a template response when no LLM is available.

        Used for testing and development without LLM access.
        This is a fallback - prefer _generate_structured_report when context is available.
        """
        return """## Clinical Report

**Note:** No clinical content was retrieved or an error occurred during generation.

Please ensure:
1. Documents have been ingested into the vector store
2. The patient has associated documents
3. Try regenerating the report

---
*If this issue persists, check the application logs for details.*
"""

    def generate_report(
        self,
        query: str,
        report_type: ReportType = ReportType.FULL_SUMMARY,
        patient_id: Optional[str] = None,
        custom_instruction: Optional[str] = None
    ) -> GeneratedReport:
        """
        Generate a clinical report using RAG.

        Args:
            query: Query describing what to summarize
            report_type: Type of report to generate
            patient_id: Optional patient ID for filtering
            custom_instruction: Optional custom instruction

        Returns:
            GeneratedReport with content and metadata
        """
        logger.info(f"Generating {report_type.value} report")

        # Retrieve relevant documents
        if patient_id:
            results = self.retriever.retrieve_for_patient(query, patient_id)
        else:
            results = self.retriever.retrieve(query)

        if not results:
            logger.warning("No relevant documents retrieved")
            return GeneratedReport(
                report_type=report_type,
                content="Unable to generate report: No relevant documents found.",
                context_used=0,
                sources=[],
                metadata={'error': 'No documents retrieved'}
            )

        # Build context
        context = self.retriever.build_context(query, results)

        # Generate report content
        if self.llm_client is None:
            # Use structured report display without LLM
            logger.info("No LLM client configured - generating structured report from retrieved content")
            content = self._generate_structured_report(context, report_type)
        else:
            # Build prompt and use LLM for synthesis
            prompts = PromptBuilder.build_prompt(
                report_type=report_type,
                context=context,
                custom_instruction=custom_instruction
            )
            content = self._generate_with_llm(
                system_prompt=prompts['system'],
                user_prompt=prompts['user']
            )

        return GeneratedReport(
            report_type=report_type,
            content=content,
            context_used=len(context.retrieved_chunks),
            sources=context.metadata.get('sources', []),
            metadata={
                'total_retrieved': context.total_chunks,
                'chars_used': context.metadata.get('chars_used', 0),
                'query': query
            }
        )

    def generate_patient_summary(
        self,
        patient_id: str,
        report_type: ReportType = ReportType.FULL_SUMMARY
    ) -> GeneratedReport:
        """
        Generate a summary for a specific patient.

        Args:
            patient_id: Patient identifier
            report_type: Type of report

        Returns:
            GeneratedReport for the patient
        """
        # Use a general query to retrieve all relevant docs for patient
        query = "clinical summary patient history treatment progress assessment"

        return self.generate_report(
            query=query,
            report_type=report_type,
            patient_id=patient_id
        )


def create_rag_system(
    vector_store: ClinicalVectorStore,
    llm_client: Optional[Any] = None
) -> ReportGenerator:
    """
    Factory function to create RAG system.

    Args:
        vector_store: Vector store with documents
        llm_client: Optional LLM client

    Returns:
        Configured ReportGenerator
    """
    retriever = ClinicalRetriever(vector_store)
    return ReportGenerator(retriever, llm_client)
