# ChromaDB Vector Database

This folder contains the ChromaDB vector database setup for storing and searching document embeddings.

## Directory Structure

```
chromadb/
├── client.py          # ChromaDB client wrapper
├── indexer.py         # Index documents into ChromaDB
├── searcher.py        # Search documents using vector similarity
├── data/              # ChromaDB persistent storage (auto-created)
└── requirements.txt   # Python dependencies
```

## Setup

1. **Install ChromaDB**:
   ```bash
   pip install chromadb==0.4.22
   ```

2. **Initialize ChromaDB**:
   The database will be automatically created in the `data/` folder when you first use it.

## Usage

### Indexing Documents

```python
from database.chromadb import ChromaDBIndexer

# Initialize indexer
indexer = ChromaDBIndexer()

# Index document summary
indexer.index_document_summary(
    document_id=123,
    summary="This is a policy document for auto insurance...",
    metadata={
        "filename": "policy.pdf",
        "content_type": "application/pdf",
        "company_id": 29447
    }
)

# Index document content chunks
chunks = ["First paragraph...", "Second paragraph...", "Third paragraph..."]
indexer.index_document_content_chunks(
    document_id=123,
    chunks=chunks,
    metadata={
        "filename": "policy.pdf",
        "content_type": "application/pdf",
        "company_id": 29447
    }
)
```

### Searching Documents

```python
from database.chromadb import ChromaDBSearcher

# Initialize searcher
searcher = ChromaDBSearcher()

# Search for relevant documents
results = searcher.search_documents(
    query="What is the coverage limit for auto insurance?",
    company_id=29447,
    top_k=5,
    similarity_threshold=0.5,
    search_summaries=True,
    search_content=True
)

# Print results
for result in results:
    print(f"Document: {result['filename']}")
    print(f"Similarity: {result['similarity']:.2%}")
    print(f"Matched text: {result['matched_text'][:200]}...")
    print()
```

## Collections

ChromaDB uses two collections:

1. **document_summaries**: Stores embeddings of document summaries
   - Fast semantic search
   - One embedding per document

2. **document_content**: Stores embeddings of document content chunks
   - Detailed content search
   - Multiple embeddings per document

## Data Storage

- **Location**: `./data/` (relative to this folder)
- **Absolute path**: `/Users/harperloaner/Desktop/priya_technical_assessment/ai_assistant/database/chromadb/data/`
- **Format**: ChromaDB persistent storage (SQLite + vectors)
- **Backup**: Simply copy the entire `data/` folder

## Features

- ✅ Local persistent storage (no external database needed)
- ✅ Fast vector similarity search
- ✅ Automatic collection management
- ✅ Support for metadata filtering
- ✅ Separate collections for summaries and content
- ✅ OpenAI text-embedding-3-small (1536 dimensions)

## Migration from PostgreSQL pgvector

This ChromaDB implementation replaces the PostgreSQL `document_embeddings` table:

| PostgreSQL pgvector | ChromaDB |
|---------------------|----------|
| `document_embeddings` table | `document_summaries` + `document_content` collections |
| HNSW index | Built-in HNSW index |
| Cosine distance | Cosine distance |
| 1536 dimensions | 1536 dimensions |

## Maintenance

### View Statistics
```python
from database.chromadb import ChromaDBIndexer

indexer = ChromaDBIndexer()
stats = indexer.get_collection_stats()
print(stats)
```

### Delete Document Embeddings
```python
indexer.delete_document_embeddings(document_id=123)
```

### Reset Database (⚠️ Deletes all data)
```python
from database.chromadb import get_chroma_client

client = get_chroma_client()
client.reset()  # USE WITH CAUTION!
```