"""MySQL Database tool for the React Agent."""

import json
import time
import mysql.connector
from mysql.connector import Error
from typing import Any, Dict, List, Optional, Tuple
from .base_tool import BaseTool, ToolResult
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MySQLConnection:
    """MySQL connection manager with connection pooling."""
    
    def __init__(self, host: str, database: str, user: str, password: str, port: int = 3306):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None
        self._table_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes cache for table schema
    
    def connect(self):
        """Establish connection to MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port,
                autocommit=True,
                charset='utf8mb4',
                use_unicode=True
            )
            logger.info(f"Successfully connected to MySQL database: {self.database}")
            return True
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.connection and self.connection.is_connected()
    
    def ensure_connection(self):
        """Ensure connection is active, reconnect if needed."""
        if not self.is_connected():
            self.connect()
    
    def execute_query(self, query: str, params: Tuple = None) -> Tuple[bool, Any, str]:
        """Execute a SQL query and return results."""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            cursor.close()
            return True, result, ""
            
        except Error as e:
            logger.error(f"MySQL query error: {e}")
            return False, None, str(e)
    
    def get_table_names(self) -> List[str]:
        """Get all table names in the database."""
        success, result, error = self.execute_query("SHOW TABLES")
        if success and result:
            # MySQL returns table names in format: {'Tables_in_dbname': 'table_name'}
            table_key = f"Tables_in_{self.database}"
            return [row[table_key] for row in result]
        return []
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information."""
        # Check cache first
        cache_key = f"{table_name}_schema"
        if (cache_key in self._table_cache and 
            time.time() - self._cache_timestamp < self._cache_ttl):
            return self._table_cache[cache_key]
        
        success, result, error = self.execute_query(f"DESCRIBE {table_name}")
        if success and result:
            schema = {
                "columns": [],
                "primary_keys": [],
                "column_types": {}
            }
            
            for column in result:
                col_name = column['Field']
                col_type = column['Type']
                is_primary = column['Key'] == 'PRI'
                
                schema["columns"].append(col_name)
                schema["column_types"][col_name] = col_type
                if is_primary:
                    schema["primary_keys"].append(col_name)
            
            # Cache the schema
            self._table_cache[cache_key] = schema
            self._cache_timestamp = time.time()
            return schema
        
        return {"columns": [], "primary_keys": [], "column_types": {}}
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        return table_name in self.get_table_names()


class MySQLDatabaseTool(BaseTool):
    """MySQL Database tool that provides database operations with real MySQL connection."""
    
    def __init__(self, host: str, database: str, user: str, password: str, port: int = 3306):
        super().__init__(
            name="mysql_database",
            description="Query and manage data in a MySQL database. Supports operations: list_tables, get, set, delete, search, stats, create_table, describe"
        )
        self.mysql = MySQLConnection(host, database, user, password, port)
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Initialize connection to MySQL database."""
        if not self.mysql.connect():
            logger.error("Failed to connect to MySQL database")
            raise Exception("Could not connect to MySQL database")
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute database operations."""
        try:
            # Parse the query to determine operation
            parts = query.strip().split()
            if not parts:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Empty query provided"
                )
            
            operation = parts[0].lower()
            
            if operation == "list_tables":
                return await self._list_tables_operation()
            elif operation == "describe" or operation == "desc":
                return await self._describe_table_operation(parts[1:])
            elif operation == "get":
                return await self._get_operation(parts[1:])
            elif operation == "set" or operation == "insert":
                return await self._set_operation(parts[1:])
            elif operation == "update":
                return await self._update_operation(parts[1:])
            elif operation == "delete":
                return await self._delete_operation(parts[1:])
            elif operation == "search":
                return await self._search_operation(parts[1:])
            elif operation == "stats":
                return await self._stats_operation()
            elif operation == "create_table":
                # Handle create_table specially to preserve parentheses content
                return await self._create_table_operation_improved(query)
            elif operation == "custom_query" or operation == "sql":
                return await self._custom_query_operation(parts[1:])
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown operation: {operation}. Supported: list_tables, describe, get, set, update, delete, search, stats, create_table, sql"
                )
        
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Database operation failed: {str(e)}"
            )
    
    async def _list_tables_operation(self) -> ToolResult:
        """Handle list tables operations."""
        tables = self.mysql.get_table_names()
        
        return ToolResult(
            success=True,
            data={"tables": tables, "count": len(tables)},
            metadata={"operation": "list_tables", "database": self.mysql.database}
        )
    
    async def _describe_table_operation(self, args: List[str]) -> ToolResult:
        """Handle describe table operations."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Describe operation requires a table name"
            )
        
        table_name = args[0]
        if not self.mysql.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' does not exist"
            )
        
        schema = self.mysql.get_table_schema(table_name)
        success, result, error = self.mysql.execute_query(f"DESCRIBE {table_name}")
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to describe table: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "table": table_name,
                "schema": result,
                "columns": schema["columns"],
                "primary_keys": schema["primary_keys"],
                "column_types": schema["column_types"]
            },
            metadata={"operation": "describe", "table": table_name}
        )
    
    async def _get_operation(self, args: List[str]) -> ToolResult:
        """Handle get operations. Format: get <table> [where_clause] or get <table> * [limit]."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Get operation requires table name"
            )
        
        table_name = args[0]
        if not self.mysql.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' does not exist"
            )
        
        # Build SELECT query
        if len(args) == 1:
            # Get all records
            query = f"SELECT * FROM {table_name} LIMIT 100"  # Limit for safety
        elif len(args) == 2 and args[1] == "*":
            # Get all records without limit
            query = f"SELECT * FROM {table_name}"
        elif len(args) >= 3 and args[1] == "*":
            # Get with limit: get table * 50
            try:
                limit = int(args[2])
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
            except ValueError:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Invalid limit value"
                )
        else:
            # Assume it's a WHERE clause or primary key
            where_clause = " ".join(args[1:])
            
            # Check if it's a simple ID lookup
            if where_clause.isdigit():
                schema = self.mysql.get_table_schema(table_name)
                if schema["primary_keys"]:
                    pk = schema["primary_keys"][0]
                    query = f"SELECT * FROM {table_name} WHERE {pk} = {where_clause}"
                else:
                    query = f"SELECT * FROM {table_name} WHERE id = {where_clause}"
            else:
                # Assume it's a WHERE clause
                query = f"SELECT * FROM {table_name} WHERE {where_clause}"
        
        success, result, error = self.mysql.execute_query(query)
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Query failed: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "table": table_name,
                "records": result,
                "count": len(result) if result else 0
            },
            metadata={"operation": "get", "table": table_name, "query": query}
        )
    
    async def _set_operation(self, args: List[str]) -> ToolResult:
        """Handle set/insert operations. Format: set <table> <json_data>."""
        if len(args) < 2:
            return ToolResult(
                success=False,
                data=None,
                error="Set operation requires table name and JSON data"
            )
        
        table_name = args[0]
        if not self.mysql.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' does not exist"
            )
        
        # Parse JSON data
        try:
            json_data = " ".join(args[1:])
            data = json.loads(json_data)
            if not isinstance(data, dict):
                raise ValueError("Data must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Invalid JSON data: {str(e)}"
            )
        
        # Build INSERT query
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        success, result, error = self.mysql.execute_query(query, tuple(values))
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Insert failed: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "table": table_name,
                "inserted_data": data,
                "affected_rows": result
            },
            metadata={"operation": "insert", "table": table_name}
        )
    
    async def _update_operation(self, args: List[str]) -> ToolResult:
        """Handle update operations. Format: update <table> <json_data> where <condition>."""
        if len(args) < 4:
            return ToolResult(
                success=False,
                data=None,
                error="Update operation requires: table, JSON data, 'where', and condition"
            )
        
        table_name = args[0]
        if not self.mysql.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' does not exist"
            )
        
        # Find 'where' keyword
        try:
            where_index = args.index("where")
            json_data = " ".join(args[1:where_index])
            where_clause = " ".join(args[where_index + 1:])
        except ValueError:
            return ToolResult(
                success=False,
                data=None,
                error="Update operation requires 'where' clause"
            )
        
        # Parse JSON data
        try:
            data = json.loads(json_data)
            if not isinstance(data, dict):
                raise ValueError("Data must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Invalid JSON data: {str(e)}"
            )
        
        # Build UPDATE query
        set_clauses = [f"{col} = %s" for col in data.keys()]
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
        
        success, result, error = self.mysql.execute_query(query, tuple(data.values()))
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Update failed: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "table": table_name,
                "updated_data": data,
                "affected_rows": result,
                "where_clause": where_clause
            },
            metadata={"operation": "update", "table": table_name}
        )
    
    async def _delete_operation(self, args: List[str]) -> ToolResult:
        """Handle delete operations. Format: delete <table> where <condition>."""
        if len(args) < 3:
            return ToolResult(
                success=False,
                data=None,
                error="Delete operation requires: table, 'where', and condition"
            )
        
        table_name = args[0]
        if not self.mysql.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' does not exist"
            )
        
        # Find 'where' keyword
        try:
            where_index = args.index("where")
            where_clause = " ".join(args[where_index + 1:])
        except ValueError:
            return ToolResult(
                success=False,
                data=None,
                error="Delete operation requires 'where' clause for safety"
            )
        
        # Build DELETE query
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        success, result, error = self.mysql.execute_query(query)
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Delete failed: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "table": table_name,
                "affected_rows": result,
                "where_clause": where_clause
            },
            metadata={"operation": "delete", "table": table_name}
        )
    
    async def _search_operation(self, args: List[str]) -> ToolResult:
        """Handle search operations across tables."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Search operation requires a search term"
            )
        
        search_term = " ".join(args)
        tables = self.mysql.get_table_names()
        results = {}
        
        for table_name in tables:
            try:
                schema = self.mysql.get_table_schema(table_name)
                
                # Build search conditions for text columns
                search_conditions = []
                for column in schema["columns"]:
                    col_type = schema["column_types"].get(column, "").lower()
                    if any(text_type in col_type for text_type in ['varchar', 'text', 'char']):
                        search_conditions.append(f"{column} LIKE %s")
                
                if search_conditions:
                    where_clause = " OR ".join(search_conditions)
                    query = f"SELECT * FROM {table_name} WHERE {where_clause}"
                    search_params = tuple([f"%{search_term}%"] * len(search_conditions))
                    
                    success, result, error = self.mysql.execute_query(query, search_params)
                    
                    if success and result:
                        results[table_name] = {
                            "records": result,
                            "count": len(result)
                        }
            
            except Exception as e:
                logger.warning(f"Error searching table {table_name}: {e}")
                continue
        
        total_results = sum(table_data["count"] for table_data in results.values())
        
        return ToolResult(
            success=True,
            data={
                "search_term": search_term,
                "results": results,
                "total_results": total_results,
                "tables_searched": list(results.keys())
            },
            metadata={"operation": "search", "term": search_term}
        )
    
    async def _stats_operation(self) -> ToolResult:
        """Handle stats operations."""
        tables = self.mysql.get_table_names()
        table_stats = {}
        total_records = 0
        
        for table in tables:
            try:
                success, result, error = self.mysql.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                if success and result:
                    count = result[0]['count']
                    table_stats[table] = {
                        "record_count": count,
                        "schema": self.mysql.get_table_schema(table)
                    }
                    total_records += count
            except Exception as e:
                logger.warning(f"Error getting stats for table {table}: {e}")
                table_stats[table] = {"record_count": "Error", "schema": {}}
        
        stats = {
            "database": self.mysql.database,
            "host": self.mysql.host,
            "total_tables": len(tables),
            "total_records": total_records,
            "tables": tables,
            "table_stats": table_stats,
            "connection_status": "connected" if self.mysql.is_connected() else "disconnected"
        }
        
        return ToolResult(
            success=True,
            data=stats,
            metadata={"operation": "stats", "database": self.mysql.database}
        )
    
    async def _create_table_operation_improved(self, query: str) -> ToolResult:
        """Handle create table operations with improved parsing. Format: create_table <table_name> (<column_definitions>)."""
        import re
        
        # Parse: create_table table_name (column definitions)
        match = re.match(r'create_table\s+(\w+)\s*\((.+)\)', query.strip(), re.IGNORECASE)
        
        if not match:
            return ToolResult(
                success=False,
                data=None,
                error="Invalid create_table format. Expected: create_table table_name (column_definitions)"
            )
        
        table_name = match.group(1)
        column_definitions = match.group(2).strip()
        
        # Basic validation
        if self.mysql.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' already exists"
            )
        
        sql_query = f"CREATE TABLE {table_name} ({column_definitions})"
        
        success, result, error = self.mysql.execute_query(sql_query)
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Create table failed: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "table_name": table_name,
                "created": True
            },
            metadata={
                "operation": "create_table",
                "table": table_name
            }
        )

    async def _create_table_operation(self, args: List[str]) -> ToolResult:
        """Handle create table operations. Format: create_table <table_name> <column_definitions>."""
        if len(args) < 2:
            return ToolResult(
                success=False,
                data=None,
                error="Create table operation requires table name and column definitions"
            )
        
        table_name = args[0]
        column_definitions = " ".join(args[1:])
        
        # Basic validation
        if self.mysql.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' already exists"
            )
        
        query = f"CREATE TABLE {table_name} ({column_definitions})"
        
        success, result, error = self.mysql.execute_query(query)
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Create table failed: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "table_name": table_name,
                "column_definitions": column_definitions,
                "created": True
            },
            metadata={"operation": "create_table", "table": table_name}
        )
    
    async def _custom_query_operation(self, args: List[str]) -> ToolResult:
        """Handle custom SQL query operations. Format: sql <query>."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="SQL operation requires a query"
            )
        
        query = " ".join(args)
        
        # Basic safety check - prevent dangerous operations
        dangerous_keywords = ['DROP', 'TRUNCATE', 'ALTER DATABASE', 'CREATE DATABASE']
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Dangerous operation '{keyword}' not allowed"
                )
        
        success, result, error = self.mysql.execute_query(query)
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Query failed: {error}"
            )
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "result": result,
                "count": len(result) if isinstance(result, list) else result
            },
            metadata={"operation": "custom_query"}
        )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "MySQL database query in format: 'operation [args...]'. Operations:\n" +
                                 "- list_tables: List all tables in database\n" +
                                 "- describe <table>: Get table schema\n" +
                                 "- get <table> [where_clause]: Get records from table\n" +
                                 "- set <table> <json_data>: Insert new record\n" +
                                 "- update <table> <json_data> where <condition>: Update existing records\n" +
                                 "- delete <table> where <condition>: Delete records\n" +
                                 "- search <term>: Search across all tables\n" +
                                 "- stats: Get database statistics\n" +
                                 "- create_table <table> <columns>: Create new table\n" +
                                 "- sql <query>: Execute custom SQL query"
                }
            },
            "required": ["query"]
        }
    
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'mysql'):
            self.mysql.disconnect()