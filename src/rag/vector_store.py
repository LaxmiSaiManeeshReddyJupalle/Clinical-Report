"""
Vector Store Module for UIC ATU Clinical Report Generator

Provides ChromaDB integration for document embeddings and retrieval.
Part of the RAG pipeline for clinical report generation.

SECURITY: Document embeddings may contain semantic information about PHI.
Handle vector store data with same security as source documents.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

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


def create_vector_store() -> ClinicalVectorStore:
    """
    Factory function to create vector store from environment.

    Returns:
        Configured ClinicalVectorStore instance
    """
    from dotenv import load_dotenv
    load_dotenv()

    persist_dir = os.environ.get('CHROMA_PERSIST_DIR', './data/chroma')
    collection_name = os.environ.get('CHROMA_COLLECTION', 'clinical_docs')

    return ClinicalVectorStore(
        persist_dir=persist_dir,
        collection_name=collection_name
    )
