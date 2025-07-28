"""Database tool with caching mechanism for the React Agent."""

import json
import time
from typing import Any, Dict, List, Optional
from .base_tool import BaseTool, ToolResult


class DatabaseCache:
    """Simple in-memory cache to mimic database operations with table support."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._tables: Dict[str, Dict[str, Any]] = {}  # table_name -> {record_id -> record_data}
        self._timestamps: Dict[str, float] = {}  # "table.record_id" -> timestamp
    
    def create_table(self, table_name: str) -> bool:
        """Create a new table."""
        if table_name in self._tables:
            return False  # Table already exists
        self._tables[table_name] = {}
        return True
    
    def list_tables(self) -> List[str]:
        """List all tables."""
        return list(self._tables.keys())
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        return table_name in self._tables
    
    def get(self, table_name: str, record_id: str) -> Optional[Any]:
        """Get record from table."""
        if table_name not in self._tables:
            return None
        
        cache_key = f"{table_name}.{record_id}"
        if record_id not in self._tables[table_name]:
            return None
        
        # Check if expired
        if cache_key in self._timestamps and time.time() - self._timestamps[cache_key] > self.ttl:
            self.delete(table_name, record_id)
            return None
        
        return self._tables[table_name][record_id]
    
    def get_table(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get entire table."""
        if table_name not in self._tables:
            return None
        
        # Clean up expired records
        expired_keys = []
        for record_id in self._tables[table_name]:
            cache_key = f"{table_name}.{record_id}"
            if cache_key in self._timestamps and time.time() - self._timestamps[cache_key] > self.ttl:
                expired_keys.append(record_id)
        
        for record_id in expired_keys:
            self.delete(table_name, record_id)
        
        return self._tables[table_name].copy()
    
    def set(self, table_name: str, record_id: str, value: Any) -> bool:
        """Set record in table."""
        if table_name not in self._tables:
            return False  # Table doesn't exist
        
        cache_key = f"{table_name}.{record_id}"
        
        # If record already exists, just update it
        if record_id in self._tables[table_name]:
            self._tables[table_name][record_id] = value
            self._timestamps[cache_key] = time.time()
            return True
        
        # Remove oldest entries if cache is full
        total_records = sum(len(table) for table in self._tables.values())
        while total_records >= self.max_size and self._timestamps:
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            table_name_old, record_id_old = oldest_key.split('.', 1)
            self.delete(table_name_old, record_id_old)
            total_records -= 1
        
        self._tables[table_name][record_id] = value
        self._timestamps[cache_key] = time.time()
        return True
    
    def delete(self, table_name: str, record_id: str) -> bool:
        """Delete record from table."""
        if table_name not in self._tables or record_id not in self._tables[table_name]:
            return False
        
        cache_key = f"{table_name}.{record_id}"
        self._tables[table_name].pop(record_id, None)
        self._timestamps.pop(cache_key, None)
        return True
    
    def delete_table(self, table_name: str) -> bool:
        """Delete entire table."""
        if table_name not in self._tables:
            return False
        
        # Remove all timestamps for this table
        keys_to_remove = [key for key in self._timestamps.keys() if key.startswith(f"{table_name}.")]
        for key in keys_to_remove:
            self._timestamps.pop(key, None)
        
        self._tables.pop(table_name, None)
        return True
    
    def clear(self) -> None:
        """Clear all cache."""
        self._tables.clear()
        self._timestamps.clear()
    
    def keys(self, table_name: Optional[str] = None) -> List[str]:
        """Get all record keys, optionally for a specific table."""
        if table_name:
            return list(self._tables.get(table_name, {}).keys())
        
        all_keys = []
        for table, records in self._tables.items():
            all_keys.extend([f"{table}.{record_id}" for record_id in records.keys()])
        return all_keys
    
    def size(self, table_name: Optional[str] = None) -> int:
        """Get current cache size, optionally for a specific table."""
        if table_name:
            return len(self._tables.get(table_name, {}))
        return sum(len(table) for table in self._tables.values())
    
    def is_full(self) -> bool:
        """Check if cache is at capacity."""
        return self.size() >= self.max_size
    
    def search_in_table(self, table_name: str, search_term: str) -> Dict[str, Any]:
        """Search for records in a specific table."""
        if table_name not in self._tables:
            return {}
        
        results = {}
        search_term_lower = search_term.lower()
        
        for record_id, record_data in self._tables[table_name].items():
            try:
                data_str = json.dumps(record_data, default=str).lower()
                if search_term_lower in data_str:
                    results[record_id] = record_data
            except (TypeError, ValueError):
                if search_term_lower in str(record_data).lower():
                    results[record_id] = record_data
        
        return results
    
    def search_all_tables(self, search_term: str) -> Dict[str, Dict[str, Any]]:
        """Search for records across all tables."""
        results = {}
        for table_name in self._tables:
            table_results = self.search_in_table(table_name, search_term)
            if table_results:
                results[table_name] = table_results
        return results


class DatabaseTool(BaseTool):
    """Database tool that mimics database operations with caching."""
    
    def __init__(self):
        super().__init__(
            name="database",
            description=self._get_detailed_description()
        )
        self.cache = DatabaseCache()
        
        # Initialize with sample tables and data
        self._initialize_sample_data()
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for database operations."""
        return """Query and store data in a cached in-memory database with table support.

WHAT IT DOES:
• Provides in-memory database functionality with table operations
• Stores and retrieves structured data temporarily
• Supports basic CRUD operations (Create, Read, Update, Delete)
• Includes built-in caching with TTL (Time To Live)

AVAILABLE OPERATIONS:

• create_table <table_name> - Create a new table
  Usage: create_table customers
  
• list - List all available tables
  Usage: list
  
• get <table> <record_id> - Retrieve specific record
  Usage: get users user123
  
• set <table> <record_id> <json_data> - Store/update record  
  Usage: set users user123 {"name": "John", "age": 30}
  
• delete <table> <record_id> - Delete specific record
  Usage: delete users user123
  
• search <table> <search_term> - Search within table
  Usage: search users john
  
• search_all <search_term> - Search across all tables
  Usage: search_all engineering
  
• stats - Show database statistics
  Usage: stats

USAGE EXAMPLES:

Creating and Using Tables:
1. create_table products
2. set products item001 {"name": "Laptop", "price": 999, "category": "electronics"}
3. get products item001
4. search products laptop

Working with Users:
- set users emp123 {"name": "Alice Smith", "department": "marketing", "salary": 55000}
- search users alice
- delete users emp123

PRE-LOADED SAMPLE DATA:
• users table: Sample user records with names, emails, roles
• admin table: Administrator accounts and permissions  
• sales table: Sales data and transaction records

DATA FORMAT:
• Records stored as JSON objects
• Each record has a unique ID within its table
• Supports nested data structures
• Automatic timestamp tracking

FEATURES:
• TTL-based cache expiration (1 hour default)
• Cross-table search capabilities
• Statistics and usage monitoring
• Table-based data organization
• JSON-based data storage

LIMITATIONS:
• Data is temporary (in-memory only)
• No persistence across application restarts
• Limited to simple query operations
• No complex joins or relationships
• Size limits for performance

BEST PRACTICES:
• Use descriptive table names
• Keep record IDs unique and meaningful
• Store related data in the same table
• Use JSON format for complex data structures"""
    
    def _initialize_sample_data(self):
        """Initialize the cache with sample tables and data."""
        # Create default tables
        self.cache.create_table("users")
        self.cache.create_table("admin") 
        self.cache.create_table("sales")
        
        # Add sample user data
        user_data = [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "role": "user", "department": "engineering"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "role": "user", "department": "marketing"},
            {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "role": "user", "department": "sales"}
        ]
        
        for user in user_data:
            self.cache.set("users", str(user["id"]), user)
        
        # Add sample admin data
        admin_data = [
            {"id": 1, "name": "Admin User", "email": "admin@example.com", "role": "admin", "permissions": ["read", "write", "delete"]},
            {"id": 2, "name": "Super Admin", "email": "superadmin@example.com", "role": "superadmin", "permissions": ["all"]}
        ]
        
        for admin in admin_data:
            self.cache.set("admin", str(admin["id"]), admin)
        
        # Add sample sales data
        sales_data = [
            {"id": 1, "name": "Sales Rep 1", "email": "sales1@example.com", "region": "north", "sales_target": 100000},
            {"id": 2, "name": "Sales Rep 2", "email": "sales2@example.com", "region": "south", "sales_target": 120000},
            {"id": 3, "name": "Sales Manager", "email": "salesmanager@example.com", "region": "all", "sales_target": 500000}
        ]
        
        for sales in sales_data:
            self.cache.set("sales", str(sales["id"]), sales)
    
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
            
            if operation == "create_table":
                return await self._create_table_operation(parts[1:])
            elif operation == "list_tables":
                return await self._list_tables_operation()
            elif operation == "get":
                return await self._get_operation(parts[1:])
            elif operation == "set":
                return await self._set_operation(parts[1:])
            elif operation == "delete":
                return await self._delete_operation(parts[1:])
            elif operation == "list":
                return await self._list_operation(parts[1:])
            elif operation == "search":
                return await self._search_operation(parts[1:])
            elif operation == "stats":
                return await self._stats_operation()
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown operation: {operation}. Supported: create_table, list_tables, get, set, delete, list, search, stats"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Database operation failed: {str(e)}"
            )
    
    async def _create_table_operation(self, args: List[str]) -> ToolResult:
        """Handle create table operations."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Create table operation requires a table name"
            )
        
        table_name = args[0]
        success = self.cache.create_table(table_name)
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' already exists"
            )
        
        return ToolResult(
            success=True,
            data={"table_name": table_name, "created": True},
            metadata={"operation": "create_table", "table": table_name}
        )
    
    async def _list_tables_operation(self) -> ToolResult:
        """Handle list tables operations."""
        tables = self.cache.list_tables()
        
        return ToolResult(
            success=True,
            data={"tables": tables, "count": len(tables)},
            metadata={"operation": "list_tables"}
        )
    
    async def _get_operation(self, args: List[str]) -> ToolResult:
        """Handle get operations. Format: get <table> <id> OR get <table> (get entire table)."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Get operation requires table name and optionally record id"
            )
        
        table_name = args[0]
        
        # If no record id provided, get entire table
        if len(args) == 1:
            data = self.cache.get_table(table_name)
            if data is None:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Table '{table_name}' not found"
                )
            return ToolResult(
                success=True,
                data=data,
                metadata={"operation": "get", "table": table_name, "type": "table"}
            )
        
        # Get specific record
        record_id = args[1]
        data = self.cache.get(table_name, record_id)
        
        if data is None:
            return ToolResult(
                success=False,
                data=None,
                error=f"Record '{record_id}' not found in table '{table_name}'"
            )
        
        return ToolResult(
            success=True,
            data=data,
            metadata={"operation": "get", "table": table_name, "record_id": record_id}
        )
    
    async def _set_operation(self, args: List[str]) -> ToolResult:
        """Handle set operations. Format: set <table> <id> <value>."""
        if len(args) < 3:
            return ToolResult(
                success=False,
                data=None,
                error="Set operation requires table name, record id, and value"
            )
        
        table_name = args[0]
        record_id = args[1]
        
        try:
            # Try to parse as JSON, otherwise treat as string
            value_str = " ".join(args[2:])
            try:
                value = json.loads(value_str)
            except json.JSONDecodeError:
                value = value_str
            
            success = self.cache.set(table_name, record_id, value)
            
            if not success:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Table '{table_name}' does not exist. Create it first."
                )
            
            return ToolResult(
                success=True,
                data={"table": table_name, "record_id": record_id, "value": value},
                metadata={"operation": "set", "table": table_name, "record_id": record_id}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to set value: {str(e)}"
            )
    
    async def _delete_operation(self, args: List[str]) -> ToolResult:
        """Handle delete operations. Format: delete <table> <id> OR delete <table> (delete entire table)."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Delete operation requires table name and optionally record id"
            )
        
        table_name = args[0]
        
        # If no record id provided, delete entire table
        if len(args) == 1:
            success = self.cache.delete_table(table_name)
            if not success:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Table '{table_name}' not found"
                )
            return ToolResult(
                success=True,
                data={"deleted_table": table_name},
                metadata={"operation": "delete", "table": table_name, "type": "table"}
            )
        
        # Delete specific record
        record_id = args[1]
        success = self.cache.delete(table_name, record_id)
        
        if not success:
            return ToolResult(
                success=False,
                data=None,
                error=f"Record '{record_id}' not found in table '{table_name}'"
            )
        
        return ToolResult(
            success=True,
            data={"deleted_record": record_id, "table": table_name},
            metadata={"operation": "delete", "table": table_name, "record_id": record_id}
        )
    
    async def _list_operation(self, args: List[str]) -> ToolResult:
        """Handle list operations. Format: list OR list <table>."""
        if not args:
            # List all record keys across all tables
            keys = self.cache.keys()
            return ToolResult(
                success=True,
                data={"keys": keys, "count": len(keys)},
                metadata={"operation": "list", "type": "all"}
            )
        
        # List records in specific table
        table_name = args[0]
        if not self.cache.table_exists(table_name):
            return ToolResult(
                success=False,
                data=None,
                error=f"Table '{table_name}' not found"
            )
        
        keys = self.cache.keys(table_name)
        return ToolResult(
            success=True,
            data={"keys": keys, "count": len(keys), "table": table_name},
            metadata={"operation": "list", "table": table_name}
        )
    
    async def _search_operation(self, args: List[str]) -> ToolResult:
        """Handle intelligent search operations. Format: search <term> OR search <table> <term>."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Search operation requires a search term"
            )
        
        # Check if first arg is a table name
        if len(args) >= 2 and self.cache.table_exists(args[0]):
            # Search in specific table
            table_name = args[0]
            search_term = " ".join(args[1:]).lower()
            
            results = self.cache.search_in_table(table_name, search_term)
            
            return ToolResult(
                success=True,
                data={table_name: results},
                metadata={"operation": "search", "table": table_name, "term": search_term, "count": len(results)}
            )
        
        # Smart search across all tables
        search_term = " ".join(args).lower()
        results = self.cache.search_all_tables(search_term)
        total_count = sum(len(table_results) for table_results in results.values())
        
        # Smart table inference based on search term context
        inferred_tables = self._infer_likely_tables(search_term)
        
        return ToolResult(
            success=True,
            data=results,
            metadata={
                "operation": "search", 
                "term": search_term, 
                "total_count": total_count,
                "tables_searched": list(results.keys()),
                "likely_tables": inferred_tables
            }
        )
    
    def _infer_likely_tables(self, search_term: str) -> List[str]:
        """Infer which tables are most likely to contain the search term based on context."""
        likely_tables = []
        
        # Define keywords that suggest specific tables
        table_keywords = {
            "users": ["user", "name", "email", "department", "employee"],
            "admin": ["admin", "permission", "superadmin", "role", "access"],
            "sales": ["sales", "rep", "manager", "target", "region", "revenue"]
        }
        
        search_lower = search_term.lower()
        
        # Score each table based on keyword matches
        table_scores = {}
        for table, keywords in table_keywords.items():
            score = sum(1 for keyword in keywords if keyword in search_lower)
            if score > 0:
                table_scores[table] = score
        
        # Return tables sorted by relevance score
        likely_tables = sorted(table_scores.keys(), key=lambda t: table_scores[t], reverse=True)
        
        return likely_tables
    
    async def _stats_operation(self) -> ToolResult:
        """Handle stats operations."""
        tables = self.cache.list_tables()
        table_stats = {}
        
        for table in tables:
            table_stats[table] = {
                "record_count": self.cache.size(table),
                "records": self.cache.keys(table)
            }
        
        stats = {
            "total_records": self.cache.size(),
            "max_size": self.cache.max_size,
            "cache_full": self.cache.is_full(),
            "ttl": self.cache.ttl,
            "tables": tables,
            "table_count": len(tables),
            "table_stats": table_stats
        }
        
        return ToolResult(
            success=True,
            data=stats,
            metadata={"operation": "stats"}
        )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Database query in format: 'operation [args...]'. Operations:\n" +
                                 "- create_table <table_name>\n" +
                                 "- list_tables\n" +
                                 "- get <table> [id] (get record or entire table)\n" +
                                 "- set <table> <id> <value>\n" +
                                 "- delete <table> [id] (delete record or entire table)\n" +
                                 "- list [table] (list records in table or all)\n" +
                                 "- search <term> OR search <table> <term>\n" +
                                 "- stats (get database statistics)"
                }
            },
            "required": ["query"]
        }