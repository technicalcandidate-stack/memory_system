"""
ChromaDB Searcher - Search document embeddings using vector similarity.
"""

from typing import List, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openai import OpenAI
from .client import get_chroma_client

# OpenAI client for generating query embeddings
openai_client = OpenAI()


class ChromaDBSearcher:
    """Search document embeddings in ChromaDB using semantic similarity."""

    def __init__(self):
        """Initialize ChromaDB searcher."""
        self.chroma_client = get_chroma_client()

        # Get collections
        self.summary_collection = self.chroma_client.get_or_create_collection(
            name="document_summaries",
            metadata={"description": "Document summary embeddings"}
        )

        self.content_collection = self.chroma_client.get_or_create_collection(
            name="document_content",
            metadata={"description": "Document content chunk embeddings"}
        )

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query using OpenAI.

        Args:
            query: Search query text

        Returns:
            Embedding vector (1536 dimensions)
        """
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        return response.data[0].embedding

    def search_documents(
        self,
        query: str,
        company_id: Optional[int] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
        search_summaries: bool = True,
        search_content: bool = False
    ) -> List[Dict]:
        """
        Search for documents using semantic similarity.

        Args:
            query: Search query text
            company_id: Filter by company ID (optional)
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            search_summaries: Search summary embeddings
            search_content: Search content chunk embeddings

        Returns:
            List of search results with similarity scores
        """
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)

        results = []

        # Search summaries
        if search_summaries:
            summary_results = self._search_collection(
                collection=self.summary_collection,
                query_embedding=query_embedding,
                company_id=company_id,
                top_k=top_k
            )
            results.extend(summary_results)

        # Search content chunks
        if search_content:
            content_results = self._search_collection(
                collection=self.content_collection,
                query_embedding=query_embedding,
                company_id=company_id,
                top_k=top_k
            )
            results.extend(content_results)

        # Filter by similarity threshold
        results = [r for r in results if r["similarity"] >= similarity_threshold]

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def _search_collection(
        self,
        collection,
        query_embedding: List[float],
        company_id: Optional[int],
        top_k: int
    ) -> List[Dict]:
        """
        Search a specific collection.

        Args:
            collection: ChromaDB collection
            query_embedding: Query embedding vector
            company_id: Filter by company ID
            top_k: Number of results

        Returns:
            List of search results
        """
        try:
            # Build where filter
            where_filter = {}
            if company_id is not None:
                where_filter["company_id"] = company_id

            # Query ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    # ChromaDB returns distances, convert to similarity (1 - distance)
                    # For cosine distance, similarity = 1 - distance
                    distance = results["distances"][0][i]
                    similarity = 1 - distance

                    metadata = results["metadatas"][0][i]

                    formatted_results.append({
                        "document_id": metadata.get("document_id"),
                        "filename": metadata.get("filename", "Unknown"),
                        "content_type": metadata.get("content_type", "Unknown"),
                        "document_summary": metadata.get("document_summary"),
                        "matched_text": results["documents"][0][i],
                        "similarity": similarity,
                        "chunk_index": metadata.get("chunk_index", 0),
                        "type": metadata.get("type", "unknown")
                    })

            return formatted_results

        except Exception as e:
            print(f"Error searching collection: {e}")
            return []

    def search_by_document_id(
        self,
        document_id: int,
        include_content: bool = True
    ) -> Dict:
        """
        Retrieve all embeddings for a specific document.

        Args:
            document_id: Document ID
            include_content: Include content chunks

        Returns:
            Dictionary with summary and content embeddings
        """
        result = {
            "document_id": document_id,
            "summary": None,
            "content_chunks": []
        }

        try:
            # Get summary
            summary_results = self.summary_collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )

            if summary_results["ids"]:
                result["summary"] = {
                    "text": summary_results["documents"][0],
                    "metadata": summary_results["metadatas"][0]
                }

            # Get content chunks
            if include_content:
                content_results = self.content_collection.get(
                    where={"document_id": document_id},
                    include=["documents", "metadatas"]
                )

                if content_results["ids"]:
                    for i in range(len(content_results["ids"])):
                        result["content_chunks"].append({
                            "text": content_results["documents"][i],
                            "metadata": content_results["metadatas"][i]
                        })

        except Exception as e:
            print(f"Error retrieving document {document_id}: {e}")

        return result