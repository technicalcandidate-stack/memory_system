"""General skill as fallback for non-specific queries."""
from .base import BaseSkill


class GeneralSkill(BaseSkill):
    """Fallback skill for queries that don't match specific skills."""

    @staticmethod
    def get_context_template() -> str:
        # Import the existing schema context
        from core.schema_loader import SCHEMA_CONTEXT
        return SCHEMA_CONTEXT

    @staticmethod
    def format_response(results: list, sql: str) -> str:
        """Generic response: describe result count."""
        if not results:
            return "Query completed but returned no results."

        count = len(results)
        columns = list(results[0].keys()) if results else []

        response = f"Found {count} result(s)"
        if columns:
            column_preview = ', '.join(columns[:5])
            response += f" with columns: {column_preview}"
            if len(columns) > 5:
                response += f" and {len(columns) - 5} more"

        return response