"""SQL syntax validation and safety checks."""
import sqlparse
from sqlparse.sql import Statement
from typing import Tuple


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Validate SQL syntax and safety.

    Args:
        sql: The SQL query string to validate

    Returns:
        (is_valid: bool, error_message: str)
        If valid, error_message will be "Valid"
    """
    if not sql or not sql.strip():
        return False, "Empty or whitespace-only SQL query"

    try:
        # Parse SQL using sqlparse
        parsed = sqlparse.parse(sql)

        if not parsed:
            return False, "Failed to parse SQL query"

        # Get the first statement
        stmt: Statement = parsed[0]

        # Check if it's a SELECT query (read-only)
        stmt_type = stmt.get_type()
        if stmt_type != 'SELECT':
            return False, f"Only SELECT queries are allowed. Found: {stmt_type}"

        # Convert to lowercase for keyword checks
        sql_lower = sql.lower()

        # Check for company_id filter (critical for multi-tenancy)
        # Allow queries without filter if they're querying the companies table directly
        # or if they're explicitly querying across multiple companies
        has_company_filter = 'matched_company_id' in sql_lower
        has_company_table = 'companies' in sql_lower or 'public.companies' in sql_lower

        # If querying communication tables, must have company filter or join with companies
        is_comm_query = any(table in sql_lower for table in ['emails_silver', 'phone_call_silver', 'phone_message_silver'])

        if is_comm_query and not has_company_filter and not has_company_table:
            return False, "Query must filter by matched_company_id or join with companies table for security"

        # Check for dangerous keywords (mutations)
        dangerous_keywords = [
            'drop', 'truncate', 'delete', 'insert',
            'update', 'alter', 'create', 'grant',
            'revoke', 'exec', 'execute'
        ]

        for keyword in dangerous_keywords:
            # Look for keyword as a whole word (not part of another word)
            if f' {keyword} ' in f' {sql_lower} ' or sql_lower.startswith(f'{keyword} '):
                return False, f"Dangerous SQL keyword detected: {keyword.upper()}"

        # Check for semicolons (prevent multiple statements)
        if sql.count(';') > 1 or (sql.count(';') == 1 and not sql.rstrip().endswith(';')):
            return False, "Multiple SQL statements not allowed"

        # Check for comment attacks
        if '--' in sql and 'matched_company_id' in sql:
            # Allow -- in SQL but check it's not commenting out the filter
            lines = sql.split('\n')
            for line in lines:
                if 'matched_company_id' in line and '--' in line:
                    # Check if -- comes before matched_company_id
                    if line.index('--') < line.index('matched_company_id'):
                        return False, "Potential comment attack on matched_company_id filter"

        return True, "Valid"

    except Exception as e:
        return False, f"SQL parsing error: {str(e)}"


def sanitize_sql(sql: str) -> str:
    """
    Sanitize SQL query by formatting it properly.

    Args:
        sql: The SQL query to sanitize

    Returns:
        Formatted SQL query
    """
    try:
        # Format SQL for better readability
        formatted = sqlparse.format(
            sql,
            reindent=True,
            keyword_case='upper',
            strip_comments=False
        )
        return formatted
    except Exception:
        # If formatting fails, return original
        return sql
