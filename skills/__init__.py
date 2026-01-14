"""Skills registry for LangChain-based text-to-SQL agent."""
from .companies_data import CompaniesDataSkill
from .email_communications import EmailCommunicationsSkill
from .phone_calls import PhoneCallsSkill
from .phone_messages import PhoneMessagesSkill
from .general import GeneralSkill

# Registry mapping skill names to skill classes
SKILL_HANDLERS = {
    "companies_data": CompaniesDataSkill,
    "email_communications": EmailCommunicationsSkill,
    "phone_calls": PhoneCallsSkill,
    "phone_messages": PhoneMessagesSkill,
    "general": GeneralSkill,
}

__all__ = [
    "SKILL_HANDLERS",
    "CompaniesDataSkill",
    "EmailCommunicationsSkill",
    "PhoneCallsSkill",
    "PhoneMessagesSkill",
    "GeneralSkill",
]