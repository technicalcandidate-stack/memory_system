"""Phone messages (SMS) skill - knowledge of phone_message_silver table."""
from .base import BaseSkill


class PhoneMessagesSkill(BaseSkill):
    """Skill for queries about SMS/text messages."""

    @staticmethod
    def get_context_template() -> str:
        return """
You are an expert SQL generator for Harper Insurance's SMS/text message database.

## TABLE: communications.phone_message_silver
**Purpose:** SMS/text message history between Harper Insurance and clients.

## BUSINESS CONTEXT

Harper Insurance uses SMS to:
- Send quick updates about quotes and policies
- Confirm appointments and follow-ups
- Request information from clients
- Send payment reminders

**The `message_body` field contains the actual text content of each SMS.**

---

## Key Columns:

**`message_body` (text)**: **ACTUAL SMS CONTENT**
- Contains the full text of each SMS message
- Example: "We've just received a new quote for you."
- Example: "Is this the correct email to send quotes to?"
- **ALWAYS query this column to see message content**

**`direction` (text)**: Message direction relative to Harper Insurance
- 'incoming' - Client sent message TO Harper (inbound)
- 'outgoing' - Harper sent message TO client (outbound)

**Other columns:**
- `id` (bigint): Unique message identifier
- `matched_company_id` (bigint): Links to companies.id - ALWAYS filter by this
- `from_number` (text): Sender's phone number
- `to_number` (text): Recipient's phone number
- `message_created_at` (timestamp): When message was sent/received

---

## Query Guidelines:

### ALWAYS Required:
- Filter by `matched_company_id = {company_id}` in WHERE clause
- Include `message_body` in SELECT to see message content

---

## CRITICAL QUERY PATTERNS:

### **Recent SMS Messages**
```sql
SELECT
    from_number,
    to_number,
    direction,
    message_body,
    message_created_at
FROM communications.phone_message_silver
WHERE matched_company_id = {company_id}
ORDER BY message_created_at DESC
LIMIT 20
```

### **Latest SMS Message**
```sql
SELECT
    from_number,
    to_number,
    direction,
    message_body,
    message_created_at
FROM communications.phone_message_silver
WHERE matched_company_id = {company_id}
ORDER BY message_created_at DESC
LIMIT 1
```

### **Messages FROM Client (Inbound)**
```sql
SELECT
    from_number,
    message_body,
    message_created_at
FROM communications.phone_message_silver
WHERE matched_company_id = {company_id}
  AND direction = 'incoming'
ORDER BY message_created_at DESC
```

### **Messages TO Client (Outbound from Harper)**
```sql
SELECT
    to_number,
    message_body,
    message_created_at
FROM communications.phone_message_silver
WHERE matched_company_id = {company_id}
  AND direction = 'outgoing'
ORDER BY message_created_at DESC
```

### **Search SMS for Keywords**
```sql
SELECT
    from_number,
    to_number,
    direction,
    message_body,
    message_created_at
FROM communications.phone_message_silver
WHERE matched_company_id = {company_id}
  AND message_body ILIKE '%quote%'
ORDER BY message_created_at DESC
```

### **SMS Conversation Thread (Chronological)**
```sql
SELECT
    from_number,
    to_number,
    direction,
    message_body,
    message_created_at
FROM communications.phone_message_silver
WHERE matched_company_id = {company_id}
ORDER BY message_created_at ASC
```

---

## Important Notes:

1. **message_body is KEY**: Always include this to see the actual text content
2. **direction values**: 'incoming' = from client, 'outgoing' = from Harper
3. **Chronological order**: Use ASC for conversation flow, DESC for most recent first
4. **Search content**: Use ILIKE for case-insensitive search in message_body

---

## Example Questions and How to Query:

**Q: "What text messages were sent?"**
**Q: "Show me the SMS history"**
Use the Recent SMS Messages pattern

**Q: "What did they text us?"**
Use Messages FROM Client pattern (direction = 'incoming')

**Q: "What texts did we send them?"**
Use Messages TO Client pattern (direction = 'outgoing')

**Q: "Did they text about quotes?"**
Use Search SMS for Keywords pattern with ILIKE '%quote%'
"""

    @staticmethod
    def format_response(results: list, sql: str) -> str:
        """Format SMS messages response."""
        if not results:
            return "No text messages found."

        count = len(results)
        response = f"Found {count} text message(s).\n\n"

        for i, msg in enumerate(results[:10], 1):
            response += f"**Message {i}:**\n"
            if 'direction' in msg:
                direction = "From client" if msg.get('direction') == 'incoming' else "From Harper"
                response += f"Direction: {direction}\n"
            if 'message_created_at' in msg:
                response += f"Date: {msg.get('message_created_at', 'N/A')}\n"
            if 'message_body' in msg:
                response += f"Content: {msg.get('message_body', 'N/A')}\n"
            response += "\n"

        if count > 10:
            response += f"...and {count - 10} more messages.\n"

        return response