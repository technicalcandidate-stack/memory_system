"""
Migrate documents from PostgreSQL to ChromaDB.
Indexes document summaries and content chunks into ChromaDB.
"""

import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

from sqlalchemy import create_engine, text
from database.chromadb.indexer import ChromaDBIndexer
import time

# Database connection
db_url = "postgresql://postgres:stuffs3reed9ruled7mouse7rot3crackpot@db.ehvopzzidrfxtvsfrfkq.supabase.co:5432/postgres?sslmode=require"
engine = create_engine(db_url)

print("=" * 80)
print("MIGRATE DOCUMENTS TO CHROMADB")
print("=" * 80)

# Initialize ChromaDB indexer
indexer = ChromaDBIndexer()

# Get initial stats
initial_stats = indexer.get_collection_stats()
print(f"\nInitial ChromaDB stats:")
print(f"  Summary embeddings: {initial_stats['summary_embeddings']}")
print(f"  Content embeddings: {initial_stats['content_embeddings']}")
print(f"  Total: {initial_stats['total_embeddings']}")

# Step 1: Get all documents with summaries and content
print("\n" + "=" * 80)
print("Step 1: Fetching documents from documents_01_14...")
print("=" * 80)

with engine.connect() as conn:
    query = text("""
    SELECT DISTINCT ON (d.id)
        d.id,
        d.metadata->>'filename' as filename,
        d.metadata->>'content_type' as content_type,
        d.parsed_content,
        d.document_summary,
        cdj.company_id
    FROM public.documents_01_14 d
    LEFT JOIN public.companies_documents_join cdj ON d.id = cdj.attachment_id
    WHERE d.document_summary IS NOT NULL OR d.parsed_content IS NOT NULL
    ORDER BY d.id
    """)

    result = conn.execute(query)
    documents = []

    for row in result:
        doc = {
            "id": row[0],
            "filename": row[1],
            "content_type": row[2],
            "parsed_content": row[3],
            "document_summary": row[4],
            "company_id": row[5]
        }
        documents.append(doc)

print(f"Found {len(documents)} documents to index")

# Step 2: Index document summaries
print("\n" + "=" * 80)
print("Step 2: Indexing document summaries...")
print("=" * 80)

summary_count = 0
summary_success = 0

for doc in documents:
    if doc["document_summary"]:
        summary_count += 1
        print(f"\nIndexing summary {summary_count}/{len(documents)}: {doc['filename']}")

        metadata = {
            "filename": doc["filename"],
            "content_type": doc["content_type"],
            "company_id": doc["company_id"],
            "document_summary": doc["document_summary"]
        }

        success = indexer.index_document_summary(
            document_id=doc["id"],
            summary=doc["document_summary"],
            metadata=metadata
        )

        if success:
            summary_success += 1

        # Small delay to avoid rate limiting
        time.sleep(0.1)

print(f"\nSummary indexing complete: {summary_success}/{summary_count} successful")

# Step 3: Index document content chunks
print("\n" + "=" * 80)
print("Step 3: Indexing document content chunks...")
print("=" * 80)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Split text into overlapping chunks."""
    if not text or len(text) < chunk_size:
        return [text] if text else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks

content_count = 0
content_success = 0

for doc in documents:
    if doc["parsed_content"]:
        content_count += 1
        print(f"\nIndexing content {content_count}/{len(documents)}: {doc['filename']}")

        # Chunk the content
        chunks = chunk_text(doc["parsed_content"], chunk_size=1000, overlap=200)
        print(f"  Created {len(chunks)} chunks")

        metadata = {
            "filename": doc["filename"],
            "content_type": doc["content_type"],
            "company_id": doc["company_id"],
            "document_summary": doc["document_summary"]
        }

        success = indexer.index_document_content_chunks(
            document_id=doc["id"],
            chunks=chunks,
            metadata=metadata
        )

        if success:
            content_success += 1

        # Small delay to avoid rate limiting
        time.sleep(0.1)

print(f"\nContent indexing complete: {content_success}/{content_count} successful")

# Step 4: Final stats
print("\n" + "=" * 80)
print("Step 4: Final Statistics")
print("=" * 80)

final_stats = indexer.get_collection_stats()
print(f"\nFinal ChromaDB stats:")
print(f"  Summary embeddings: {final_stats['summary_embeddings']}")
print(f"  Content embeddings: {final_stats['content_embeddings']}")
print(f"  Total: {final_stats['total_embeddings']}")

print(f"\nAdded:")
print(f"  Summary embeddings: +{final_stats['summary_embeddings'] - initial_stats['summary_embeddings']}")
print(f"  Content embeddings: +{final_stats['content_embeddings'] - initial_stats['content_embeddings']}")
print(f"  Total: +{final_stats['total_embeddings'] - initial_stats['total_embeddings']}")

print("\n" + "=" * 80)
print("MIGRATION COMPLETE!")
print("=" * 80)

print(f"""
Summary:
- Documents processed: {len(documents)}
- Summaries indexed: {summary_success}/{summary_count}
- Content documents indexed: {content_success}/{content_count}
- Total embeddings: {final_stats['total_embeddings']}

ChromaDB is ready to use!
Storage location: {os.path.join(os.path.dirname(__file__), 'data')}
""")