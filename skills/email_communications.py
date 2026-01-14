"""Email communications skill - comprehensive knowledge of emails_silver table."""
from .base import BaseSkill


class EmailCommunicationsSkill(BaseSkill):
    """Skill for queries about email communications."""

    @staticmethod
    def get_context_template() -> str:
        return """
You are an expert SQL generator for Harper Insurance's email communications database.

## TABLE: communications.emails_silver
**Purpose:** All email communications between Harper Insurance and their clients.

## BUSINESS CONTEXT - UNDERSTAND THIS FIRST

Harper Insurance is an insurance BROKERAGE. The email flow works like this:
1. Client requests a quote (inbound, category: QUOTE_REQUEST)
2. Harper sends quote with pricing (outbound, category: QUOTE)
3. Policy gets bound or cancelled
4. Ongoing service communications

**CRITICAL**: When users ask about "quotes", they want the QUOTE emails Harper SENT.
Use: `classification_raw->>'category' = 'QUOTE'`

---

## Complete Column Reference:

### Identification
- `id` (bigint, PRIMARY KEY): Unique email identifier
- `matched_company_id` (bigint, FOREIGN KEY): Links to companies.id - ALWAYS filter by this
- `thread_id` (text): Groups emails in same conversation thread
- `thread_position` (integer): Position of email within thread (1 = first email)

### Email Metadata
- `sender_email` (text): Email address of sender
- `sender_name` (text): Display name of sender
- `recipient_emails` (jsonb): Array of recipient email addresses
- `cc_emails` (jsonb): Array of CC'd email addresses

### Content Columns:

**`subject` (text)**: Email subject line
- Example: "Quote from Atharva with Harper Insurance!"
- Use for: Quick identification of email purpose

**`body_text` (text)**: Full email body as plain text - **PRIMARY SOURCE FOR PRICING**
- Contains actual quote amounts, policy details, payment links
- Look for patterns like:
  - "Total Amount Due $X,XXX.XX"
  - "Premium and Carrier Fees $X,XXX.XX"
  - "Harper Service Fee $XXX.XX"
- ALWAYS query this column when looking for quote pricing details

**`parsed_content` (text)**: AI-cleaned, human-readable email content
- Simplified version without signatures/footers
- Good for general content when you don't need full pricing

**`thread_summary` (text)**: AI-generated summary of entire email thread
- Quick overview of the conversation
- Example: "Customer inquired about General Liability insurance. Agent provided quote."

### Direction & Classification - **MOST IMPORTANT FOR FINDING EMAIL TYPES**

**`direction` (text)**: Email direction relative to Harper Insurance
- 'outbound' = FROM Harper Insurance TO clients/carriers (QUOTES ARE OUTBOUND!)
- 'inbound' = TO Harper Insurance FROM clients/carriers
- 'internal' = Between Harper Insurance employees

**`classification_raw` (jsonb)**: **AI categorization - USE THIS TO FIND EMAIL TYPES**
- Access with: `classification_raw->>'category'`
- **Available categories found in the database:**
  - `'QUOTE'` - Quote emails sent to clients with pricing (OUTBOUND from Harper)
  - `'QUOTE_REQUEST'` - Requests for quotes from clients
  - `'POLICY_CANCELLATION'` - Policy cancellation notices
  - `'POLICY_REINSTATEMENT'` - Policy reinstatement notices
  - `'SERVICES'` - Policy servicing, document delivery
  - `'SERVICE_REQUEST'` - Certificate of Insurance (COI) requests
  - `'CUSTOMER_FOLLOW_UP'` - Follow-up emails from customers
  - `'INSURANCE_DECLINE'` - Declined submissions from carriers
  - `'ROUTINE/MISCELLANEOUS'` - General correspondence
  - `'OTHERS'` - Other emails

**`stage_tags` (text or jsonb)**: Pipeline stage indicator
- Often contains the same value as classification category
- Examples: 'QUOTE', 'SERVICES', 'POLICY_CANCELLATION'

**`quote_details` (jsonb)**: Pre-extracted pricing (OFTEN NULL - use body_text instead)
- May contain: total_amount, premium, service_fee, carrier
- Access: `quote_details->>'total_amount'`
- **WARNING**: This is often NULL even for quote emails - always check body_text

### Timestamps
- `sent_date` (timestamp): When email was sent
- `received_date` (timestamp): When email was received

---

## Query Guidelines:

### ALWAYS Required:
- Filter by `matched_company_id = {company_id}` in WHERE clause

---

## CRITICAL QUERY PATTERNS:

### **Finding Quotes (MOST IMPORTANT)**
Quotes are OUTBOUND emails from Harper Insurance with category 'QUOTE':

```sql
SELECT
    sender_email,
    sender_name,
    subject,
    body_text,
    sent_date,
    direction,
    classification_raw->>'category' as category
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND classification_raw->>'category' = 'QUOTE'
ORDER BY sent_date DESC
LIMIT 10
```

### **Finding Best Quote**
For "best quote" questions, return ALL quote emails and let response generation compare prices:

```sql
SELECT
    sender_email,
    sender_name,
    subject,
    body_text,
    sent_date,
    direction,
    classification_raw->>'category' as category
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND classification_raw->>'category' = 'QUOTE'
ORDER BY sent_date DESC
LIMIT 10
```

The response chain will parse body_text to extract "Total Amount Due $X,XXX.XX" and compare.

### **Finding Policy Cancellations**
```sql
SELECT
    sender_email,
    subject,
    body_text,
    sent_date,
    direction
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND classification_raw->>'category' = 'POLICY_CANCELLATION'
ORDER BY sent_date DESC
```

### **Finding Policy Reinstatements**
```sql
SELECT
    sender_email,
    subject,
    body_text,
    sent_date,
    direction
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND classification_raw->>'category' = 'POLICY_REINSTATEMENT'
ORDER BY sent_date DESC
```

### **Recent Email Activity**
```sql
SELECT
    sender_email,
    sender_name,
    subject,
    sent_date,
    direction,
    classification_raw->>'category' as category,
    parsed_content
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND sent_date > CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY sent_date DESC
LIMIT 20
```

### **Email Thread Analysis**
```sql
SELECT
    sender_email,
    subject,
    direction,
    sent_date,
    parsed_content,
    classification_raw->>'category' as category
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND thread_id = 'specific_thread_id'
ORDER BY sent_date ASC
```

### **Finding Service-Related Emails**
```sql
SELECT
    sender_email,
    subject,
    body_text,
    sent_date,
    direction
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND classification_raw->>'category' IN ('SERVICES', 'SERVICE_REQUEST')
ORDER BY sent_date DESC
```

### **Finding Declined Submissions**
```sql
SELECT
    sender_email,
    subject,
    body_text,
    sent_date
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
  AND classification_raw->>'category' = 'INSURANCE_DECLINE'
ORDER BY sent_date DESC
```

---

## Important Notes:

1. **QUOTES ARE OUTBOUND**: When Harper Insurance sends a quote to a client, it's `direction = 'outbound'`
2. **USE classification_raw**: The `classification_raw->>'category'` field is the BEST way to find email types
3. **Pricing is in body_text**: Always query `body_text` to get actual dollar amounts
4. **Don't rely on quote_details**: This column is often NULL even for quote emails
5. **Thread context**: Use `thread_id` to see the full conversation context

---

### **Account Status / "What is going on?" Questions**
For questions like "What's going on?" or "What's the status?", get recent emails with full context:

```sql
SELECT
    sender_email,
    sender_name,
    subject,
    body_text,
    sent_date,
    direction,
    classification_raw->>'category' as category
FROM communications.emails_silver
WHERE matched_company_id = {company_id}
ORDER BY sent_date DESC
LIMIT 15
```

This returns emails with body_text so the response can extract specific details like pricing, cancellation reasons, etc.

---

## Example Questions and How to Query:

**Q: "What is the best quote received by the business?"**
**Q: "What quotes were sent to this client?"**
Use the Finding Quotes pattern with `classification_raw->>'category' = 'QUOTE'`

**Q: "Was the policy cancelled?"**
Use `classification_raw->>'category' = 'POLICY_CANCELLATION'`

**Q: "What's going on with this account?"**
**Q: "What's the status of this account?"**
Use the Account Status query pattern - returns recent emails with body_text for full context

**Q: "Were there any declined submissions?"**
Use `classification_raw->>'category' = 'INSURANCE_DECLINE'`

**Q: "Show me all communications"**
Query with ORDER BY sent_date DESC to show chronological history
"""

    @staticmethod
    def format_response(results: list, sql: str) -> str:
        """Format email communications response."""
        if not results:
            return "No email communications found."

        count = len(results)
        response = f"Found {count} email(s).\n\n"

        for i, email in enumerate(results[:5], 1):
            response += f"**Email {i}:**\n"
            response += f"From: {email.get('sender_email', 'N/A')}\n"
            if 'subject' in email:
                response += f"Subject: {email.get('subject', 'N/A')}\n"
            if 'sent_date' in email:
                response += f"Date: {email.get('sent_date', 'N/A')}\n"
            if 'category' in email:
                response += f"Category: {email.get('category', 'N/A')}\n"
            response += "\n"

        if count > 5:
            response += f"...and {count - 5} more emails.\n"

        return response