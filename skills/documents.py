"""Documents skill - comprehensive knowledge of documents table."""
from .base import BaseSkill


class DocumentsSkill(BaseSkill):
    """Skill for queries about company documents."""

    @staticmethod
    def get_context_template() -> str:
        return """
You are an expert SQL generator for Harper Insurance's document management system.

## TABLE: public.documents_01_14
**Purpose:** Store document files with their parsed content and AI-generated summaries for insurance accounts.

## Complete Column Reference:

**`id` (bigint)**: Unique document identifier
- Primary identifier for documents

**`object_hash` (text)**: Hash of the document object
- Used for deduplication and integrity verification

**`bucket_name` (text)**: S3 bucket name
- Storage location for the document file

**`object_name` (text)**: S3 object key/path
- Full path to the document in S3 storage

**`metadata` (jsonb)**: Document metadata in JSON format
- `filename` (text): Original filename (e.g., "Policy_Document.pdf")
- `file_size` (integer): Size in bytes
- `content_type` (text): MIME type (e.g., "application/pdf")
- Access with: `metadata->>'filename'`, `metadata->>'file_size'`, `metadata->>'content_type'`

**`created_at` (timestamp with time zone)**: When record was created in database
- Useful for sorting and filtering by upload time

**`event_at` (timestamp with time zone)**: When the document event occurred
- May represent document creation or upload event time

**`parsed_content` (text)**: Extracted text content from document
- Full text extracted from PDF/document files
- Available for selected documents that have been processed
- Can be searched for specific terms or information

**`parsed_at` (timestamp with time zone)**: When document was parsed
- Timestamp indicating when text extraction occurred

**`document_summary` (text)**: AI-generated summary of document content
- Concise overview of the document's key information
- Generated using AI for documents with parsed_content
- Available for documents that have been summarized

## JOIN TABLE: public.companies_documents_join
**Purpose:** Links documents to companies (many-to-many relationship)
- `company_id` (bigint, FK): Links to companies.id
- `attachment_id` (bigint, FK): Links to documents_01_14.id

## CRITICAL QUERY PATTERNS:

### List All Documents for a Company
```sql
SELECT d.id,
       d.metadata->>'filename' as filename,
       d.metadata->>'content_type' as content_type,
       d.metadata->>'file_size' as file_size,
       d.parsed_content IS NOT NULL as has_content,
       d.document_summary IS NOT NULL as has_summary,
       d.created_at,
       d.parsed_at
FROM public.documents_01_14 d
JOIN public.companies_documents_join cdj ON d.id = cdj.attachment_id
WHERE cdj.company_id = {company_id}
ORDER BY d.created_at DESC
```

### Get Documents with Summaries
```sql
SELECT d.id,
       d.metadata->>'filename' as filename,
       d.document_summary,
       d.created_at
FROM public.documents_01_14 d
JOIN public.companies_documents_join cdj ON d.id = cdj.attachment_id
WHERE cdj.company_id = {company_id}
  AND d.document_summary IS NOT NULL
ORDER BY d.created_at DESC
```

### Get Documents with Full Content
```sql
SELECT d.id,
       d.metadata->>'filename' as filename,
       d.parsed_content,
       d.document_summary,
       d.created_at,
       d.parsed_at
FROM public.documents_01_14 d
JOIN public.companies_documents_join cdj ON d.id = cdj.attachment_id
WHERE cdj.company_id = {company_id}
  AND d.parsed_content IS NOT NULL
ORDER BY d.created_at DESC
```

### Count Documents by Type
```sql
SELECT d.metadata->>'content_type' as content_type,
       COUNT(*) as document_count,
       COUNT(d.parsed_content) as parsed_count,
       COUNT(d.document_summary) as summary_count
FROM public.documents_01_14 d
JOIN public.companies_documents_join cdj ON d.id = cdj.attachment_id
WHERE cdj.company_id = {company_id}
GROUP BY d.metadata->>'content_type'
ORDER BY document_count DESC
```

## IMPORTANT NOTES:
- Always use the JOIN with companies_documents_join to filter by company_id
- The metadata field is JSONB - use ->> operator to extract text values
- Not all documents have parsed_content or document_summary - check for NULL
- Use ORDER BY d.created_at DESC to show newest documents first
- For S3 access, combine bucket_name and object_name fields
"""

    @staticmethod
    def format_response(results: list, sql: str) -> str:
        if not results:
            return "No documents found for this company."
        count = len(results)
        response = f"Found {count} document(s):\n\n"
        for i, doc in enumerate(results[:5], 1):
            filename = doc.get('filename', 'Unknown')
            content_type = doc.get('content_type', 'Unknown')
            has_content = doc.get('has_content', False)
            has_summary = doc.get('has_summary', False)
            response += f"**{i}. {filename}** ({content_type})\n"
            response += f"   - Content: {'Yes' if has_content else 'No'} | Summary: {'Yes' if has_summary else 'No'}\n"
        if count > 5:
            response += f"...and {count - 5} more documents.\n"
        return response
