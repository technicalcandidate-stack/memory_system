"""
ChromaDB client for vector storage and retrieval.
Replaces PostgreSQL pgvector with local ChromaDB storage.
"""

import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional

# Get the absolute path to the chromadb storage directory
CHROMADB_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMADB_PERSIST_DIR = os.path.join(CHROMADB_DIR, "data")


class ChromaDBClient:
    """Singleton client for ChromaDB vector database."""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaDBClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize ChromaDB client with persistent storage."""
        if self._client is None:
            # Create persist directory if it doesn't exist
            os.makedirs(CHROMADB_PERSIST_DIR, exist_ok=True)

            # Initialize ChromaDB client with persistent storage
            self._client = chromadb.PersistentClient(
                path=CHROMADB_PERSIST_DIR,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            print(f"ChromaDB initialized at: {CHROMADB_PERSIST_DIR}")

    def get_client(self) -> chromadb.PersistentClient:
        """Get the ChromaDB client instance."""
        return self._client

    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict] = None
    ) -> chromadb.Collection:
        """
        Get or create a collection in ChromaDB.

        Args:
            name: Collection name
            metadata: Optional metadata for the collection

        Returns:
            ChromaDB collection
        """
        return self._client.get_or_create_collection(
            name=name,
            metadata=metadata or {}
        )

    def delete_collection(self, name: str):
        """Delete a collection from ChromaDB."""
        try:
            self._client.delete_collection(name=name)
            print(f"Deleted collection: {name}")
        except Exception as e:
            print(f"Error deleting collection {name}: {e}")

    def list_collections(self) -> List[str]:
        """List all collections in ChromaDB."""
        collections = self._client.list_collections()
        return [col.name for col in collections]

    def reset(self):
        """Reset ChromaDB (delete all data). Use with caution!"""
        self._client.reset()
        print("ChromaDB reset complete - all data deleted")


# Global client instance
def get_chroma_client() -> ChromaDBClient:
    """Get the global ChromaDB client instance."""
    return ChromaDBClient()