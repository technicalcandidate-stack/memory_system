"""Skill router for detecting and routing user questions to appropriate database tables."""


class SkillDetector:
    """Classify user questions into database-schema skills based on keywords."""

    # Overview keywords - HIGHEST priority for multi-table account overview questions
    OVERVIEW_KEYWORDS = [
        "what's going on", "what is going on", "whats going on",
        "account status", "account overview", "overall status",
        "what happened", "activity", "timeline", "history",
        "communications", "all communications", "recent activity",
        "latest activity", "recent communications", "update me"
    ]

    # Priority keywords - checked in order, first match wins
    PRIORITY_KEYWORDS = {
        # Documents - for file/document related questions
        "documents": [
            "document", "documents", "file", "files",
            "pdf", "png", "jpg", "jpeg", "image", "images",
            "attachment", "attachments", "upload", "uploaded",
            "download", "policy document", "certificate",
            "contract", "contracts", "paperwork"
        ],
        # Phone calls - HIGHEST priority for call-related questions
        "phone_calls": [
            "call", "calls", "phone call", "called", "calling",
            "voicemail", "recording", "discussed", "conversation",
            "talk", "talked", "spoke", "spoken", "ring", "rang",
            "answered", "unanswered", "missed call"
        ],
        # SMS/Text messages
        "phone_messages": [
            "sms", "text", "text message", "texted", "texting",
            "message sent", "message received"
        ],
        # Email communications
        "email_communications": [
            "quote", "quotes", "quoted", "pricing", "premium", "best quote",
            "cheapest quote", "lowest quote", "quote received", "quote details",
            "quote breakdown", "total amount", "amount due",
            "email", "emails", "sent", "received", "inbox",
            "subject", "sender", "recipient", "thread",
            "followup", "follow up", "unanswered", "pending",
            "awaiting response", "no reply"
        ],
    }

    # Secondary keywords - only used if no priority keywords match
    SECONDARY_KEYWORDS = {
        "companies_data": [
            "company name", "business name", "contact", "contact info",
            "contact details", "address", "phone number", "email address",
            "industry", "revenue", "employees", "website", "location",
            "business details", "company info", "company profile",
            "how many employees", "what industry", "annual revenue",
            "bold penguin id", "business information"
        ],
    }

    @staticmethod
    def detect_skill(question: str) -> str:
        """
        Detect the skill type from user question based on database tables.

        Priority order:
        1. Check overview keywords (account status, what's going on) → general (multi-table UNION)
        2. Check documents keywords (document, file, pdf, attachment)
        3. Check phone_calls keywords (calls, conversations, voicemails)
        4. Check phone_messages keywords (SMS, texts)
        5. Check email_communications keywords (quotes, emails)
        6. Check companies_data keywords - LOWEST PRIORITY

        Args:
            question: User's natural language question

        Returns:
            Skill name: general | documents | phone_calls | phone_messages | email_communications | companies_data
        """
        question_lower = question.lower()

        # FIRST: Check for overview/account status questions
        # These should use UNION ALL to query all communication tables
        if any(kw in question_lower for kw in SkillDetector.OVERVIEW_KEYWORDS):
            return "general"

        # SECOND: Check priority keywords in order
        for skill, keywords in SkillDetector.PRIORITY_KEYWORDS.items():
            if any(kw in question_lower for kw in keywords):
                return skill

        # THIRD: Check secondary keywords (company data)
        for skill, keywords in SkillDetector.SECONDARY_KEYWORDS.items():
            if any(kw in question_lower for kw in keywords):
                return skill

        # Default to general skill if no keywords match
        return "general"