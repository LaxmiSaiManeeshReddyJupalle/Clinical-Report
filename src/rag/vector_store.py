"""
Vector Store Module for UIC ATU Clinical Report Generator

Provides ChromaDB integration for document embeddings and retrieval.
Part of the RAG pipeline for clinical report generation.

SECURITY: Document embeddings may contain semantic information about PHI.
Handle vector store data with same security as source documents.
"""

import os
import logging
import hashlib
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings

# Configure logging (no PHI)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of document for embedding."""
    text: str
    metadata: Dict[str, Any]
    doc_id: str


@dataclass
class RetrievalResult:
    """Result from a vector store query."""
    text: str
    metadata: Dict[str, Any]
    distance: float
    doc_id: str

    @property
    def relevance_score(self) -> float:
        """Convert distance to relevance score (0-1, higher is better)."""
        # ChromaDB uses L2 distance by default
        return 1.0 / (1.0 + self.distance)


class ClinicalVectorStore:
    """
    ChromaDB-based vector store for clinical documents.

    Stores document embeddings for semantic search and retrieval.

    SECURITY NOTICE:
    - Embeddings encode semantic content from PHI documents
    - Persist directory should have restricted access
    - Metadata should NOT contain raw patient identifiers
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: str = "clinical_docs"
    ):
        """
        Initialize vector store.

        Args:
            persist_dir: Directory for persistent storage. None for in-memory.
            collection_name: Name of the ChromaDB collection.
        """
        self.persist_dir = persist_dir or os.environ.get('CHROMA_PERSIST_DIR')
        self.collection_name = collection_name

        # Initialize ChromaDB client
        if self.persist_dir:
            logger.info("Initializing persistent vector store")
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            logger.info("Initializing in-memory vector store")
            self._client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Clinical document embeddings"}
        )

        logger.info(f"Vector store initialized. Collection: {self.collection_name}")

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None
    ) -> int:
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects
            embeddings: Optional pre-computed embeddings

        Returns:
            Number of documents added
        """
        if not chunks:
            return 0

        ids = [chunk.doc_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        try:
            if embeddings:
                self._collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            else:
                # Let ChromaDB compute embeddings
                self._collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )

            logger.info(f"Added {len(chunks)} document chunks to vector store")
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to add documents: {type(e).__name__}")
            raise

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.

        Args:
            query_text: Query text for semantic search
            n_results: Maximum number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            Dictionary with 'documents', 'metadatas', 'distances'
        """
        try:
            results = self._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_metadata
            )

            logger.info(f"Query returned {len(results.get('documents', [[]])[0])} results")
            return results

        except Exception as e:
            logger.error(f"Query failed: {type(e).__name__}")
            raise

    def search(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Search for similar documents and return structured results.

        Args:
            query_text: Query text for semantic search
            n_results: Maximum number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of RetrievalResult objects sorted by relevance
        """
        raw_results = self.query(query_text, n_results, filter_metadata)

        results = []
        documents = raw_results.get('documents', [[]])[0]
        metadatas = raw_results.get('metadatas', [[]])[0]
        distances = raw_results.get('distances', [[]])[0]
        ids = raw_results.get('ids', [[]])[0]

        for doc, meta, dist, doc_id in zip(documents, metadatas, distances, ids):
            results.append(RetrievalResult(
                text=doc,
                metadata=meta,
                distance=dist,
                doc_id=doc_id
            ))

        return results

    def delete_by_metadata(self, filter_metadata: Dict[str, Any]) -> None:
        """
        Delete documents matching metadata filter.

        Args:
            filter_metadata: Metadata filter for deletion
        """
        try:
            self._collection.delete(where=filter_metadata)
            logger.info("Documents deleted from vector store")
        except Exception as e:
            logger.error(f"Delete failed: {type(e).__name__}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        return {
            "name": self.collection_name,
            "count": self._collection.count(),
            "persist_dir": self.persist_dir
        }

    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Clinical document embeddings"}
            )
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Clear failed: {type(e).__name__}")
            raise


def create_vector_store(
    persist_dir: Optional[str] = None,
    collection_name: Optional[str] = None
) -> ClinicalVectorStore:
    """
    Factory function to create vector store from environment.

    Args:
        persist_dir: Override persist directory
        collection_name: Override collection name

    Returns:
        Configured ClinicalVectorStore instance
    """
    from dotenv import load_dotenv
    load_dotenv()

    persist_dir = persist_dir or os.environ.get('CHROMA_PERSIST_DIR', './data/chroma')
    collection_name = collection_name or os.environ.get('CHROMA_COLLECTION', 'clinical_docs')

    return ClinicalVectorStore(
        persist_dir=persist_dir,
        collection_name=collection_name
    )


class DocumentIngestionPipeline:
    """
    Pipeline for ingesting documents into the vector store.

    Combines document processing, PII scrubbing, and vector storage.

    SECURITY: Handles PHI documents throughout the pipeline.
    """

    def __init__(
        self,
        vector_store: ClinicalVectorStore,
        scrub_pii: bool = True,
        chunk_size: int = 800,
        chunk_overlap: int = 100
    ):
        """
        Initialize ingestion pipeline.

        Args:
            vector_store: Vector store for document storage
            scrub_pii: Whether to scrub PII before storage
            chunk_size: Target chunk size for document splitting
            chunk_overlap: Overlap between chunks
        """
        self.vector_store = vector_store
        self.scrub_pii = scrub_pii
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Lazy load processor and scrubber
        self._processor = None
        self._scrubber = None

    @property
    def processor(self):
        """Lazy load document processor."""
        if self._processor is None:
            from src.ingestion.document_processor import DocumentProcessor
            self._processor = DocumentProcessor(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        return self._processor

    @property
    def scrubber(self):
        """Lazy load PII scrubber."""
        if self._scrubber is None:
            from src.ingestion.scrubber import HealthcarePIIScrubber
            self._scrubber = HealthcarePIIScrubber()
        return self._scrubber

    def _generate_chunk_id(self, source: str, chunk_index: int, text: str) -> str:
        """Generate unique ID for a chunk."""
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"{Path(source).stem}_{chunk_index}_{content_hash}"

    def ingest_document(
        self,
        file_path: Union[str, Path],
        content: Optional[bytes] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a single document into the vector store.

        Args:
            file_path: Path to the document
            content: Optional pre-loaded content
            additional_metadata: Extra metadata to include

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Processing document for ingestion")

        # Process document
        processed = self.processor.process_file(
            file_path,
            content=content,
            additional_metadata=additional_metadata
        )

        if not processed.success:
            return {
                'success': False,
                'error': processed.error_message,
                'chunks_added': 0
            }

        # Convert to vector store chunks
        chunks = []
        for proc_chunk in processed.chunks:
            # Optionally scrub PII
            text = proc_chunk.text
            if self.scrub_pii:
                scrub_result = self.scrubber.scrub(text)
                text = scrub_result.scrubbed_text

            # Generate unique ID
            doc_id = self._generate_chunk_id(
                str(file_path),
                proc_chunk.chunk_index,
                text
            )

            # Build metadata (sanitize for ChromaDB - no nested dicts)
            metadata = {
                'source': str(Path(file_path).name),
                'chunk_index': proc_chunk.chunk_index,
                'document_type': processed.document_type.value,
                'total_chunks': len(processed.chunks),
                **(additional_metadata or {})
            }

            # ChromaDB requires flat metadata values
            metadata = {k: str(v) if isinstance(v, (list, dict)) else v
                       for k, v in metadata.items()}

            chunks.append(DocumentChunk(
                text=text,
                metadata=metadata,
                doc_id=doc_id
            ))

        # Add to vector store
        added = self.vector_store.add_documents(chunks)

        return {
            'success': True,
            'chunks_added': added,
            'total_chars': processed.total_chars,
            'source': str(file_path)
        }

    def ingest_patient_documents(
        self,
        file_paths: List[Union[str, Path]],
        patient_id: str,
        year: str
    ) -> Dict[str, Any]:
        """
        Ingest all documents for a patient.

        Args:
            file_paths: List of document paths
            patient_id: Anonymized patient identifier
            year: Fiscal year

        Returns:
            Dictionary with ingestion statistics
        """
        total_chunks = 0
        successful = 0
        failed = 0

        for file_path in file_paths:
            result = self.ingest_document(
                file_path,
                additional_metadata={
                    'patient_id': patient_id,
                    'fiscal_year': year
                }
            )

            if result['success']:
                total_chunks += result['chunks_added']
                successful += 1
            else:
                failed += 1

        logger.info(f"Ingested {successful}/{len(file_paths)} documents for patient")

        return {
            'total_documents': len(file_paths),
            'successful': successful,
            'failed': failed,
            'total_chunks': total_chunks
        }

    def ingest_mock_data(self, mock_data_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Ingest all mock data into the vector store.

        Args:
            mock_data_path: Path to mock_data directory

        Returns:
            Dictionary with overall ingestion statistics
        """
        mock_path = Path(mock_data_path)

        if not mock_path.exists():
            return {'success': False, 'error': 'Mock data path not found'}

        total_documents = 0
        total_chunks = 0
        total_patients = 0

        # Iterate through fiscal years
        for fy_dir in mock_path.iterdir():
            if not fy_dir.is_dir() or not fy_dir.name.upper().startswith('FY'):
                continue

            year = fy_dir.name

            # Iterate through patient folders
            for patient_dir in fy_dir.iterdir():
                if not patient_dir.is_dir():
                    continue

                patient_id = patient_dir.name
                files = list(patient_dir.glob('*.txt'))

                if files:
                    result = self.ingest_patient_documents(
                        files,
                        patient_id=patient_id,
                        year=year
                    )
                    total_documents += result['successful']
                    total_chunks += result['total_chunks']
                    total_patients += 1

        logger.info(f"Mock data ingestion complete: {total_patients} patients, "
                   f"{total_documents} documents, {total_chunks} chunks")

        return {
            'success': True,
            'patients': total_patients,
            'documents': total_documents,
            'chunks': total_chunks
        }


def create_ingestion_pipeline(
    persist_dir: Optional[str] = None,
    scrub_pii: bool = True
) -> DocumentIngestionPipeline:
    """
    Factory function to create document ingestion pipeline.

    Args:
        persist_dir: Vector store persist directory
        scrub_pii: Whether to scrub PII

    Returns:
        Configured DocumentIngestionPipeline
    """
    vector_store = create_vector_store(persist_dir=persist_dir)
    return DocumentIngestionPipeline(
        vector_store=vector_store,
        scrub_pii=scrub_pii
    )
