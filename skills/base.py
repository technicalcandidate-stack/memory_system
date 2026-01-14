"""Base skill interface for all skill handlers."""


class BaseSkill:
    """Base class for all skills."""

    @staticmethod
    def get_context_template() -> str:
        """
        Return skill-specific schema context for the LLM.

        This context will be used as the system prompt when generating SQL.

        Returns:
            Formatted string with schema information and query guidelines
        """
        raise NotImplementedError("Subclasses must implement get_context_template()")

    @staticmethod
    def format_response(results: list, sql: str) -> str:
        """
        Generate natural language response from SQL results.

        Args:
            results: List of dicts from SQL query execution
            sql: The executed SQL query

        Returns:
            Natural language response string
        """
        raise NotImplementedError("Subclasses must implement format_response()")

    @staticmethod
    def get_examples() -> list:
        """
        Return skill-specific example questions and SQL queries.

        Returns:
            List of dicts with 'question' and 'sql' keys
        """
        return []