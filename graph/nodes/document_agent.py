"""Document Agent node for LangGraph multi-agent orchestration."""

from typing import Dict, Any, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import chromadb

from ..state import MultiAgentState, AgentResponse
from config.database import get_db_session

# Initialize ChromaDB client directly (simpler approach)
_chroma_client = None

def _get_chroma_client():
    """Get ChromaDB client (lazy initialization)."""
    global _chroma_client
    if _chroma_client is None:
        chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'database', 'chromadb', 'data')
        _chroma_client = chromadb.PersistentClient(path=chroma_path)
    return _chroma_client


def _retrieve_company_documents(company_id: int) -> List[dict]:
    """Retrieve all documents for a company."""
    sql = """
    SELECT d.id, d.metadata->>'filename' as filename, d.metadata->>'content_type' as content_type,
           d.metadata->>'file_size' as file_size, d.parsed_content, d.document_summary,
           d.bucket_name, d.object_name, d.created_at
    FROM public.documents_01_14 d
    JOIN public.companies_documents_join cdj ON d.id = cdj.attachment_id
    WHERE cdj.company_id = :company_id ORDER BY d.created_at DESC
    """
    session = get_db_session()
    try:
        result = session.execute(text(sql), {"company_id": company_id})
        documents = []
        for row in result:
            doc = {"id": row[0], "filename": row[1], "content_type": row[2], "file_size": row[3],
                   "parsed_content": row[4], "document_summary": row[5], "bucket_name": row[6],
                   "object_name": row[7], "created_at": str(row[8]) if row[8] else None}
            documents.append(doc)
        return documents
    finally:
        session.close()


def _search_document_content(documents: List[dict], search_terms: List[str]) -> List[dict]:
    """Search for terms within parsed document content."""
    results = []
    for doc in documents:
        content = doc.get("parsed_content")
        if not content:
            continue
        content_lower = content.lower()
        matches = []
        for term in search_terms:
            if term.lower() in content_lower:
                idx = content_lower.find(term.lower())
                start, end = max(0, idx - 100), min(len(content), idx + len(term) + 100)
                matches.append({"term": term, "snippet": f"...{content[start:end]}..."})
        if matches:
            results.append({"id": doc["id"], "filename": doc["filename"], "content_type": doc["content_type"],
                           "matches": matches, "full_content": content[:2000] if len(content) > 2000 else content})
    return results


def _get_all_company_documents_from_chromadb(company_id: int) -> List[dict]:
    """
    Get ALL document summaries for a company from ChromaDB.

    Simple approach: No similarity filtering - just get all documents for the company
    and let the LLM find the relevant information.

    This works because:
    - Each company has ~5-28 documents max
    - All summaries fit easily in LLM context (~7k tokens worst case)
    - LLM is better at finding specific info than vector similarity

    Args:
        company_id: Company ID to filter by

    Returns:
        List of all document summaries for the company
    """
    try:
        client = _get_chroma_client()
        collection = client.get_collection('document_summaries')

        # Get ALL documents for this company (no similarity threshold)
        results = collection.get(
            where={'company_id': company_id},
            include=['documents', 'metadatas']
        )

        # Format results
        documents = []
        if results['ids']:
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                documents.append({
                    'document_id': metadata.get('document_id'),
                    'filename': metadata.get('filename', 'Unknown'),
                    'content_type': metadata.get('content_type', 'Unknown'),
                    'summary': results['documents'][i],  # The actual summary text
                    'type': metadata.get('type', 'summary')
                })

        return documents

    except Exception as e:
        print(f"ChromaDB retrieval failed: {e}")
        return []


def _format_company_documents(documents: List[dict]) -> str:
    """Format all company documents for LLM context."""
    if not documents:
        return "No documents found for this company."

    formatted = f"**All Documents for this Company ({len(documents)} total):**\n\n"

    for i, doc in enumerate(documents, 1):
        formatted += f"**Document {i}: {doc['filename']}**\n"
        formatted += f"- Type: {doc['content_type']}\n"
        formatted += f"- Document ID: {doc.get('document_id', 'N/A')}\n"

        # Include the full summary
        if doc.get("summary"):
            formatted += f"\n**Summary:**\n{doc['summary']}\n"

        formatted += "\n" + "-"*60 + "\n\n"

    return formatted


def _format_documents_for_llm(documents: List[dict], with_content: bool = False) -> str:
    """Format documents for LLM (OLD - kept for fallback)."""
    if not documents:
        return "No documents found for this company."
    parts = []
    parsed_docs = [d for d in documents if d.get("parsed_content")]
    metadata_only = [d for d in documents if not d.get("parsed_content")]
    if parsed_docs:
        parts.append(f"**Documents with searchable content ({len(parsed_docs)}):**")
        for doc in parsed_docs[:5]:
            parts.append(f"- {doc['filename']} ({doc['content_type']})")
            if doc.get("document_summary"):
                parts.append(f"  Summary: {doc['document_summary'][:200]}...")
            if with_content and doc.get("parsed_content"):
                parts.append(f"  Content preview: {doc['parsed_content'][:500]}...")
    if metadata_only:
        parts.append(f"\n**Documents with metadata only ({len(metadata_only)}):**")
        for doc in metadata_only[:5]:
            parts.append(f"- {doc['filename']} ({doc['content_type']})")
    return "\n".join(parts)


def document_agent_node(state: MultiAgentState) -> Dict[str, Any]:
    """Document Agent node - retrieves all company documents and lets LLM find the answer."""
    print("\n" + "="*60)
    print("DOCUMENT AGENT NODE - Company Document Retrieval")
    print("="*60)

    company_id = state["company_id"]
    question = state["user_question"]

    print(f"Retrieving all documents for company {company_id}...")
    print(f"Question: {question}")

    # Get ALL documents for this company from ChromaDB (no similarity filtering)
    company_docs = _get_all_company_documents_from_chromadb(company_id)
    print(f"Found {len(company_docs)} documents for company")

    # Log documents for trace
    if company_docs:
        print("\n📄 COMPANY DOCUMENTS:")
        print("="*60)
        for i, doc in enumerate(company_docs, 1):
            print(f"\n📄 Document {i}: {doc['filename']}")
            print(f"   Type: {doc.get('content_type', 'N/A')}")
            print(f"   Document ID: {doc.get('document_id', 'N/A')}")
            if doc.get("summary"):
                summary_preview = doc["summary"][:300]
                print(f"   Summary preview: {summary_preview}...")
            print("-"*40)

    # Format all documents for LLM
    docs_info = _format_company_documents(company_docs)
    print(f"\n📝 Formatted docs info length: {len(docs_info)} characters")

    # Also retrieve full document metadata from PostgreSQL
    documents = _retrieve_company_documents(company_id)

    print("Generating natural language response...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a document analyst for Harper Insurance. You have access to ALL document summaries for this company.

## YOUR TASK:
Search through the document summaries below and find the answer to the user's question.

## DOCUMENTS:
{documents}

## INSTRUCTIONS:
1. Read through ALL the document summaries above
2. Find the specific information the user is asking about
3. Quote the exact values from the summaries (premiums, dates, coverage types, etc.)
4. Cite which document contains the information

## RESPONSE FORMAT:
- Start with the direct answer
- Quote the specific text from the document
- Reference the document filename

## EXAMPLE:
User: "What is the premium?"
Response: "According to **NXTKCJ99LW-00-GL-policy-0000.pdf**, the premium is **$1,036.00**. The document states: 'Premium: $1,036.00'"

## IMPORTANT:
- The answer IS in the documents - search carefully
- If you truly cannot find the answer, say which document might contain it"""),
        ("human", "{question}")
    ])

    try:
        chain = prompt | llm
        response = chain.invoke({"documents": docs_info, "question": question})
        natural_response = response.content
    except Exception as e:
        print(f"LLM response generation failed: {e}")
        natural_response = docs_info if company_docs else "No documents found for this company."

    # Set confidence based on whether we found documents
    confidence = 0.85 if company_docs else 0.3

    agent_response = AgentResponse(agent_name="document_agent", content=natural_response, data=None, sql=None,
                                   documents=documents, confidence=confidence, error=None)

    print(f"Document Agent completed (confidence: {confidence})")
    print("="*60 + "\n")

    return {"agent_responses": [agent_response], "retrieved_documents": documents,
            "document_summary": natural_response, "execution_path": ["document_agent"]}
