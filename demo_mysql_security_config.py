#!/usr/bin/env python3
"""
MySQL Database Security Configuration Demo

This script demonstrates how to configure MySQL database operations
to enable/disable specific operations like CREATE, UPDATE, DELETE, etc.
while keeping only search operations enabled.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.mysql_database_tool import MySQLDatabaseTool, MYSQL_AVAILABLE
from config import Config

async def demo_mysql_security_config():
    """Demonstrate MySQL security configuration."""
    
    print("🔒 MySQL Database Security Configuration Demo")
    print("=" * 60)
    
    if not MYSQL_AVAILABLE:
        print("❌ MySQL connector not available. Please install mysql-connector-python")
        return
    
    # MySQL connection configuration
    mysql_config = {
        "host": "localhost",
        "port": 3306,
        "database": "react_agent_db",
        "user": "root",
        "password": "root"
    }
    
    try:
        # Initialize MySQL tool (will automatically load config from config.py)
        print(f"🔧 Initializing MySQL tool with configuration...")
        tool = MySQLDatabaseTool(**mysql_config)
        
        print(f"📊 Current Configuration:")
        print(f"   - Read-only mode: {tool.read_only_mode}")
        print(f"   - Allowed operations: {tool._get_allowed_operations_list()}")
        print()
        
        # Test different operations
        test_operations = [
            "help",                     # Should always work
            "list_tables",             # Should work (read operation)
            "stats",                   # Should work (read operation)  
            'set test_table {"name": "John", "age": 25}',  # Should be blocked (write operation)
            'update test_table {"age": 30} WHERE id=1',     # Should be blocked (write operation)
            'delete test_table WHERE id=1',                 # Should be blocked (write operation)
            'create_table new_table (id INT, name VARCHAR(50))',  # Should be blocked (schema operation)
            'sql INSERT INTO test_table (name) VALUES ("test")',  # Should be blocked (write operation)
            'sql SELECT * FROM information_schema.tables LIMIT 5',  # Should work (read operation)
        ]
        
        print("🧪 Testing Operations:")
        print("-" * 40)
        
        for i, operation in enumerate(test_operations, 1):
            print(f"\n{i}. Testing: {operation}")
            try:
                result = await tool.execute(operation)
                if result.success:
                    print(f"   ✅ SUCCESS: Operation allowed")
                    if operation == "help":
                        # Show configuration status from help
                        config_status = result.data.get("configuration_status", {})
                        print(f"   📊 Config: {config_status}")
                    elif "data" in result.data and isinstance(result.data["data"], dict):
                        print(f"   📄 Data: {list(result.data['data'].keys()) if result.data['data'] else 'Empty'}")
                else:
                    print(f"   🔒 BLOCKED: {result.error}")
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🔧 Configuration Explanation:")
        print("-" * 30)
        print("The MySQL tool is configured via config.py with the following settings:")
        print()
        print("1. MYSQL_READ_ONLY_MODE = True")
        print("   - Forces all write operations to be disabled")
        print("   - Only allows SELECT, DESCRIBE, SHOW operations")
        print()
        print("2. MYSQL_OPERATIONS = {")
        print("   'allow_select': True,      # GET operations ✅")
        print("   'allow_search': True,      # SEARCH operations ✅")
        print("   'allow_describe': True,    # DESCRIBE operations ✅")
        print("   'allow_list_tables': True, # LIST_TABLES operations ✅")
        print("   'allow_stats': True,       # Stats operations ✅")
        print("   'allow_insert': False,     # INSERT/SET operations ❌")
        print("   'allow_update': False,     # UPDATE operations ❌")
        print("   'allow_delete': False,     # DELETE operations ❌")
        print("   'allow_create_table': False, # CREATE TABLE operations ❌")
        print("   'allow_custom_sql': False,   # Custom SQL operations ❌")
        print("}")
        print()
        print("✨ This configuration ensures only search/read operations work!")
        
        print("\n" + "=" * 60)
        print("📝 How to Modify Configuration:")
        print("-" * 35)
        print("1. Edit config.py file")
        print("2. Set MYSQL_READ_ONLY_MODE = False to allow write operations")
        print("3. Set individual permissions in MYSQL_OPERATIONS dict")
        print("4. Restart the application")
        print()
        print("Example - To allow only SELECT and INSERT:")
        print("MYSQL_OPERATIONS = {")
        print("    'allow_select': True,")
        print("    'allow_insert': True,")
        print("    'allow_update': False,")
        print("    'allow_delete': False,")
        print("    # ... other permissions")
        print("}")
        
    except Exception as e:
        print(f"❌ Failed to initialize MySQL tool: {e}")
        print("\nPossible causes:")
        print("- MySQL server not running")
        print("- Incorrect connection credentials")
        print("- Database doesn't exist")
        print("- MySQL connector not installed")

def show_config_file_example():
    """Show example of how to modify config file."""
    print("\n" + "=" * 60)
    print("📋 Complete Config File Example (config.py)")
    print("=" * 60)
    
    config_example = '''
# MySQL Database Operations Configuration
# Enable/disable specific database operations for security
MYSQL_OPERATIONS = {
    # Read operations (always safe)
    "allow_select": True,           # SELECT queries
    "allow_search": True,           # SEARCH operations
    "allow_describe": True,         # DESCRIBE/SHOW table structure
    "allow_list_tables": True,      # LIST_TABLES operation
    "allow_stats": True,            # Database statistics
    "allow_help": True,             # Help operation
    
    # Write operations (can modify data)
    "allow_insert": False,          # INSERT/SET operations
    "allow_update": False,          # UPDATE operations
    "allow_delete": False,          # DELETE operations
    
    # Schema operations (can modify structure)
    "allow_create_table": False,    # CREATE TABLE operations
    "allow_drop_table": False,      # DROP TABLE operations
    "allow_alter_table": False,     # ALTER TABLE operations
    
    # Advanced operations
    "allow_custom_sql": False,      # Custom SQL queries (sql command)
    "allow_dangerous_operations": False,  # DROP, TRUNCATE, etc.
}

# Read-only mode: if True, all write operations are disabled
MYSQL_READ_ONLY_MODE = True

# Example configurations for different scenarios:

# Scenario 1: Complete read-only (current default)
# MYSQL_READ_ONLY_MODE = True
# All write operations automatically disabled

# Scenario 2: Allow only specific write operations  
# MYSQL_READ_ONLY_MODE = False
# MYSQL_OPERATIONS["allow_insert"] = True
# MYSQL_OPERATIONS["allow_update"] = True
# Keep delete and schema operations disabled

# Scenario 3: Full access (development mode)
# MYSQL_READ_ONLY_MODE = False
# Set all allow_* permissions to True
'''
    
    print(config_example)

if __name__ == "__main__":
    print("🚀 Starting MySQL Security Configuration Demo...")
    asyncio.run(demo_mysql_security_config())
    show_config_file_example()
    print("\n✨ Demo completed!")