"""Phone calls skill - knowledge of phone_call_silver table."""
from .base import BaseSkill


class PhoneCallsSkill(BaseSkill):
    """Skill for queries about phone call conversations."""

    @staticmethod
    def get_context_template() -> str:
        return """
You are an expert SQL generator for Harper Insurance's phone call database.

## TABLE: communications.phone_call_silver
**Purpose:** Phone call history with AI-generated summaries and transcripts.

## BUSINESS CONTEXT - THE STORY IS IN recording_summary

**The `recording_summary` field contains AI-generated summaries of what was ACTUALLY DISCUSSED on each call.**

This is the PRIMARY SOURCE for understanding:
- What the customer was concerned about
- What Harper's team explained or offered
- What the outcome was
- What follow-ups are needed

**ALWAYS include recording_summary in your SELECT when querying calls.**

---

## Key Columns:

**`recording_summary` (text)**: **PRIMARY SOURCE FOR CALL CONTEXT**
- AI-generated summary of the entire call
- Contains: what was discussed, customer concerns, outcomes, next steps
- Example: "Customer called concerned about policy cancellation. Harper clarified policy was canceled due to nonpayment. Discussed reinstatement options."
- **ALWAYS query this column**

**`classification_raw` (jsonb)**: Call intent categorization
- Access: `classification_raw->>'call_intent'`
- Categories: 'SERVICE_REQUEST', 'VOICEMAIL', etc.

**`type` (text)**: Call outcome - CRITICAL for filtering
- 'answered' - Call was connected, conversation happened → HAS recording_summary
- 'unanswered_with_voicemail' - No answer, voicemail left
- 'unanswered_no_voicemail' - Missed call, no voicemail

**`direction` (text)**: Call direction relative to Harper Insurance
- 'incoming' - Customer called Harper
- 'outgoing' - Harper called customer

**Other columns:**
- `id` (bigint): Unique call identifier
- `matched_company_id` (bigint): Links to companies.id - ALWAYS filter by this
- `from_number` (text): Caller's phone number
- `to_number` (text): Recipient's phone number
- `call_created_at` (timestamp): When call occurred
- `answered_at` (timestamp): When call was answered
- `completed_at` (timestamp): When call ended

---

## Query Guidelines:

### ALWAYS Required:
- Filter by `matched_company_id = {company_id}` in WHERE clause
- Include `recording_summary` in SELECT for call context

---

## CRITICAL QUERY PATTERNS:

### **Latest Phone Call Conversation**
For "latest call" or "recent call" questions:

```sql
SELECT
    from_number,
    to_number,
    direction,
    type,
    call_created_at,
    recording_summary,
    classification_raw->>'call_intent' as call_intent
FROM communications.phone_call_silver
WHERE matched_company_id = {company_id}
  AND type = 'answered'
  AND recording_summary IS NOT NULL
ORDER BY call_created_at DESC
LIMIT 1
```

### **All Recent Calls with Context**
```sql
SELECT
    from_number,
    to_number,
    direction,
    type,
    call_created_at,
    recording_summary,
    classification_raw->>'call_intent' as call_intent
FROM communications.phone_call_silver
WHERE matched_company_id = {company_id}
ORDER BY call_created_at DESC
LIMIT 10
```

### **Answered Calls Only (Actual Conversations)**
```sql
SELECT
    from_number,
    to_number,
    direction,
    call_created_at,
    recording_summary,
    classification_raw->>'call_intent' as call_intent
FROM communications.phone_call_silver
WHERE matched_company_id = {company_id}
  AND type = 'answered'
ORDER BY call_created_at DESC
LIMIT 10
```

### **Missed/Unanswered Calls**
```sql
SELECT
    from_number,
    to_number,
    direction,
    type,
    call_created_at
FROM communications.phone_call_silver
WHERE matched_company_id = {company_id}
  AND type IN ('unanswered_with_voicemail', 'unanswered_no_voicemail')
ORDER BY call_created_at DESC
LIMIT 10
```

### **Service Request Calls**
```sql
SELECT
    from_number,
    to_number,
    direction,
    call_created_at,
    recording_summary
FROM communications.phone_call_silver
WHERE matched_company_id = {company_id}
  AND classification_raw->>'call_intent' = 'SERVICE_REQUEST'
ORDER BY call_created_at DESC
```

---

## Important Notes:

1. **recording_summary is KEY**: Always include this to understand what was discussed
2. **type = 'answered'**: Use this to filter for actual conversations
3. **direction values**: 'incoming' = customer called, 'outgoing' = Harper called
4. **For "latest conversation"**: Filter by type = 'answered' AND recording_summary IS NOT NULL

---

## Example Questions and How to Query:

**Q: "What is the latest phone call conversation?"**
**Q: "What was discussed on the last call?"**
Use the Latest Phone Call Conversation pattern with type = 'answered'

**Q: "Were there any missed calls?"**
Use the Missed/Unanswered Calls pattern

**Q: "What calls happened this week?"**
Use All Recent Calls pattern with date filter

**Q: "Did they call about their policy?"**
Use Service Request Calls pattern or search recording_summary
"""

    @staticmethod
    def format_response(results: list, sql: str) -> str:
        """Format phone calls response."""
        if not results:
            return "No phone calls found."

        count = len(results)
        response = f"Found {count} phone call(s).\n\n"

        for i, call in enumerate(results[:5], 1):
            response += f"**Call {i}:**\n"
            if 'direction' in call:
                response += f"Direction: {call.get('direction', 'N/A')}\n"
            if 'type' in call:
                response += f"Type: {call.get('type', 'N/A')}\n"
            if 'call_created_at' in call:
                response += f"Date: {call.get('call_created_at', 'N/A')}\n"
            if 'recording_summary' in call and call['recording_summary']:
                summary = call['recording_summary'][:300] + "..." if len(str(call['recording_summary'])) > 300 else call['recording_summary']
                response += f"Summary: {summary}\n"
            response += "\n"

        if count > 5:
            response += f"...and {count - 5} more calls.\n"

        return response