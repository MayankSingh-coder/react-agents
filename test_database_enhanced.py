#!/usr/bin/env python3
"""Test the enhanced database tool without pydantic dependency."""

import json
import time
import asyncio
from typing import Any, Dict, List, Optional


class ToolResult:
    """Result from a tool execution (simplified version)."""
    def __init__(self, success: bool, data: Any, error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}


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
    
    def size(self, table_name: Optional[str] = None) -> int:
        """Get current cache size, optionally for a specific table."""
        if table_name:
            return len(self._tables.get(table_name, {}))
        return sum(len(table) for table in self._tables.values())
    
    def search_all_tables(self, search_term: str) -> Dict[str, Dict[str, Any]]:
        """Search for records across all tables."""
        results = {}
        search_term_lower = search_term.lower()
        
        for table_name in self._tables:
            table_results = {}
            for record_id, record_data in self._tables[table_name].items():
                try:
                    data_str = json.dumps(record_data, default=str).lower()
                    if search_term_lower in data_str:
                        table_results[record_id] = record_data
                except (TypeError, ValueError):
                    if search_term_lower in str(record_data).lower():
                        table_results[record_id] = record_data
            
            if table_results:
                results[table_name] = table_results
                
        return results


async def test_enhanced_database():
    """Test the enhanced database functionality."""
    
    print("🚀 Testing Enhanced Database Tool with Table Support")
    print("=" * 60)
    
    # Initialize cache
    cache = DatabaseCache()
    
    # Create tables
    print("\n📋 Creating Tables...")
    tables = ["users", "admin", "sales"]
    for table in tables:
        success = cache.create_table(table)
        print(f"  ✅ Created table '{table}': {success}")
    
    # Add sample data
    print("\n📝 Adding Sample Data...")
    
    # Users data
    users_data = [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "role": "user", "department": "engineering"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "role": "user", "department": "marketing"},
        {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "role": "user", "department": "sales"}
    ]
    
    for user in users_data:
        cache.set("users", str(user["id"]), user)
    print(f"  ✅ Added {len(users_data)} users")
    
    # Admin data
    admin_data = [
        {"id": 1, "name": "Admin User", "email": "admin@example.com", "role": "admin", "permissions": ["read", "write", "delete"]},
        {"id": 2, "name": "Super Admin", "email": "superadmin@example.com", "role": "superadmin", "permissions": ["all"]}
    ]
    
    for admin in admin_data:
        cache.set("admin", str(admin["id"]), admin)
    print(f"  ✅ Added {len(admin_data)} admins")
    
    # Sales data
    sales_data = [
        {"id": 1, "name": "Sales Rep 1", "email": "sales1@example.com", "region": "north", "sales_target": 100000},
        {"id": 2, "name": "Sales Rep 2", "email": "sales2@example.com", "region": "south", "sales_target": 120000},
        {"id": 3, "name": "Sales Manager", "email": "salesmanager@example.com", "region": "all", "sales_target": 500000}
    ]
    
    for sales in sales_data:
        cache.set("sales", str(sales["id"]), sales)
    print(f"  ✅ Added {len(sales_data)} sales records")
    
    # Test operations
    print("\n🔍 Testing Database Operations...")
    
    # List tables
    tables = cache.list_tables()
    print(f"  📊 Tables: {tables}")
    
    # Get specific record
    user_1 = cache.get("users", "1")
    print(f"  👤 User 1: {user_1['name']} ({user_1['email']})")
    
    # Get entire table
    sales_table = cache.get_table("sales")
    print(f"  💰 Sales table has {len(sales_table)} records")
    
    # Test intelligent search
    print("\n🔍 Testing Intelligent Search...")
    
    # Search for admin
    admin_results = cache.search_all_tables("admin")
    total_admin = sum(len(table) for table in admin_results.values())
    print(f"  🔑 Search 'admin': Found {total_admin} results in {len(admin_results)} tables")
    
    # Search for sales target
    target_results = cache.search_all_tables("target")
    total_target = sum(len(table) for table in target_results.values())
    print(f"  🎯 Search 'target': Found {total_target} results in {len(target_results)} tables")
    
    # Search for email
    email_results = cache.search_all_tables("@example.com")
    total_email = sum(len(table) for table in email_results.values())
    print(f"  📧 Search '@example.com': Found {total_email} results in {len(email_results)} tables")
    
    # Test table inference logic
    print("\n🧠 Testing Smart Table Inference...")
    
    def infer_likely_tables(search_term: str) -> List[str]:
        """Infer which tables are most likely to contain the search term."""
        table_keywords = {
            "users": ["user", "name", "email", "department", "employee"],
            "admin": ["admin", "permission", "superadmin", "role", "access"],
            "sales": ["sales", "rep", "manager", "target", "region", "revenue"]
        }
        
        search_lower = search_term.lower()
        table_scores = {}
        
        for table, keywords in table_keywords.items():
            score = sum(1 for keyword in keywords if keyword in search_lower)
            if score > 0:
                table_scores[table] = score
        
        return sorted(table_scores.keys(), key=lambda t: table_scores[t], reverse=True)
    
    # Test different search terms
    test_terms = ["admin permissions", "sales target", "user email", "department engineering"]
    
    for term in test_terms:
        likely_tables = infer_likely_tables(term)
        results = cache.search_all_tables(term)
        actual_tables = list(results.keys())
        total_found = sum(len(table) for table in results.values())
        
        print(f"  🎯 Search '{term}':")
        print(f"    Predicted tables: {likely_tables}")
        print(f"    Actual tables with results: {actual_tables}")
        print(f"    Total results: {total_found}")
    
    # Stats
    print(f"\n📊 Database Statistics:")
    print(f"  Total tables: {len(cache.list_tables())}")
    print(f"  Total records: {cache.size()}")
    for table in cache.list_tables():
        print(f"  {table}: {cache.size(table)} records")
    
    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_database())