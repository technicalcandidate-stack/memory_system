"""Skill router for detecting and routing user questions to appropriate database tables."""


class SkillDetector:
    """Classify user questions into database-schema skills based on keywords."""

    # Priority keywords - checked in order, first match wins
    PRIORITY_KEYWORDS = {
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
            "awaiting response", "no reply", "timeline", "activity",
            "history", "communications", "what's going on", "what is going on",
            "account status", "what happened", "recent", "latest"
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
        1. Check phone_calls keywords (calls, conversations, voicemails)
        2. Check phone_messages keywords (SMS, texts)
        3. Check email_communications keywords (quotes, emails, account status)
        4. Check companies_data keywords - LOWEST PRIORITY

        Args:
            question: User's natural language question

        Returns:
            Skill name: phone_calls | phone_messages | email_communications | companies_data | general
        """
        question_lower = question.lower()

        # First: Check priority keywords in order
        for skill, keywords in SkillDetector.PRIORITY_KEYWORDS.items():
            if any(kw in question_lower for kw in keywords):
                return skill

        # Second: Check secondary keywords (company data)
        for skill, keywords in SkillDetector.SECONDARY_KEYWORDS.items():
            if any(kw in question_lower for kw in keywords):
                return skill

        # Default to general skill if no keywords match
        return "general"