import trino
from typing import Optional, List, Dict, Any
from loguru import logger
from settings import settings

class TrinoDBOperator:
    def __init__(self, schema:str):
        """
        Initialize Trino database connection

        Args:
            host: Trino coordinator host
            port: Trino coordinator port (default: 8080)
            user: Username for authentication
            catalog: Trino catalog to use
            schema: Schema within the catalog
        """
        self.schema = schema
        self.connection = None

    def connect(self) -> None:
        """Establish connection to Trino"""
        try:
            self.connection = trino.dbapi.connect(
                host=settings.TRINO_HOST,
                port=settings.TRINO_PORT,
                user=settings.TRINO_USER,
                catalog=settings.TRINO_CATALOG,
                schema=self.schema
            )
            logger.info(f"Connected to Trino at {settings.TRINO_HOST}:{settings.TRINO_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Trino: {e}")
            raise

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a query and return results

        Args:
            query: SQL query string

        Returns:
            List of dictionaries representing query results
        """
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all results
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]

            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_insert(self, query: str) -> int:
        """
        Execute an insert/update/delete query

        Args:
            query: SQL query string

        Returns:
            Number of affected rows
        """
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            affected_rows = cursor.rowcount

            logger.info(f"Insert/Update/Delete executed, {affected_rows} rows affected")
            return affected_rows

        except Exception as e:
            logger.error(f"Insert/Update/Delete execution failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def close(self) -> None:
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Trino connection closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
