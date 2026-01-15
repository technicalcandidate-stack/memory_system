"""
ChromaDB Indexer - Store document embeddings in ChromaDB.
"""

from typing import List, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openai import OpenAI
from .client import get_chroma_client

# OpenAI client for generating embeddings
openai_client = OpenAI()


class ChromaDBIndexer:
    """Index document embeddings in ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB indexer."""
        self.chroma_client = get_chroma_client()

        # Create collections for summaries and content
        self.summary_collection = self.chroma_client.get_or_create_collection(
            name="document_summaries",
            metadata={"description": "Document summary embeddings"}
        )

        self.content_collection = self.chroma_client.get_or_create_collection(
            name="document_content",
            metadata={"description": "Document content chunk embeddings"}
        )

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions)
        """
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def index_document_summary(
        self,
        document_id: int,
        summary: str,
        metadata: Dict
    ) -> bool:
        """
        Index a document summary in ChromaDB.

        Args:
            document_id: Document ID
            summary: Document summary text
            metadata: Additional metadata (filename, content_type, company_id, etc.)

        Returns:
            True if successful
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(summary)

            # Store in ChromaDB
            self.summary_collection.add(
                embeddings=[embedding],
                documents=[summary],
                metadatas=[{
                    "document_id": document_id,
                    "type": "summary",
                    **metadata
                }],
                ids=[f"doc_{document_id}_summary"]
            )

            print(f"Indexed summary for document {document_id}")
            return True

        except Exception as e:
            print(f"Error indexing summary for document {document_id}: {e}")
            return False

    def index_document_content_chunks(
        self,
        document_id: int,
        chunks: List[str],
        metadata: Dict
    ) -> bool:
        """
        Index document content chunks in ChromaDB.

        Args:
            document_id: Document ID
            chunks: List of text chunks
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            embeddings = []
            documents = []
            metadatas = []
            ids = []

            for idx, chunk in enumerate(chunks):
                # Generate embedding for chunk
                embedding = self.generate_embedding(chunk)

                embeddings.append(embedding)
                documents.append(chunk)
                metadatas.append({
                    "document_id": document_id,
                    "type": "content_chunk",
                    "chunk_index": idx,
                    **metadata
                })
                ids.append(f"doc_{document_id}_chunk_{idx}")

            # Batch add to ChromaDB
            self.content_collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            print(f"Indexed {len(chunks)} content chunks for document {document_id}")
            return True

        except Exception as e:
            print(f"Error indexing content chunks for document {document_id}: {e}")
            return False

    def delete_document_embeddings(self, document_id: int):
        """
        Delete all embeddings for a document.

        Args:
            document_id: Document ID
        """
        try:
            # Delete from summary collection
            self.summary_collection.delete(
                where={"document_id": document_id}
            )

            # Delete from content collection
            self.content_collection.delete(
                where={"document_id": document_id}
            )

            print(f"Deleted embeddings for document {document_id}")

        except Exception as e:
            print(f"Error deleting embeddings for document {document_id}: {e}")

    def get_collection_stats(self) -> Dict:
        """Get statistics about indexed documents."""
        summary_count = self.summary_collection.count()
        content_count = self.content_collection.count()

        return {
            "summary_embeddings": summary_count,
            "content_embeddings": content_count,
            "total_embeddings": summary_count + content_count
        }