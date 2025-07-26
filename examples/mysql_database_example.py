#!/usr/bin/env python3
"""
Example usage of MySQL Database Tool with React Agent.
Shows how to integrate real MySQL database with the agent system.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.enhanced_tool_manager import EnhancedToolManager
from mysql_config import MySQLConfig
from agent.react_agent import ReactAgent


async def demo_mysql_database_integration():
    """Demonstrate MySQL database integration with React Agent."""
    
    print("🚀 MySQL Database Integration Demo")
    print("=" * 45)
    
    # Option 1: Use MySQL database
    print("\n🔧 Setting up MySQL Database Tool...")
    mysql_config = MySQLConfig.get_config()
    MySQLConfig.print_config(mysql_config)
    
    if not MySQLConfig.validate_config(mysql_config):
        print("❌ Invalid MySQL configuration. Please set environment variables.")
        print("🔄 Falling back to in-memory database for demo...")
        use_mysql = False
    else:
        use_mysql = True
    
    # Initialize enhanced tool manager
    try:
        tool_manager = EnhancedToolManager(use_mysql=use_mysql, mysql_config=mysql_config)
        print(f"✅ Tool Manager initialized: {tool_manager}")
        
        # Show database status
        db_status = tool_manager.get_database_status()
        print(f"\n📊 Database Status:")
        for key, value in db_status.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Failed to initialize tool manager: {e}")
        return
    
    # Test database operations
    print(f"\n🧪 Testing Database Operations...")
    
    db_tool_name = tool_manager.get_database_tool_name()
    print(f"Using database tool: {db_tool_name}")
    
    # Basic operations test
    test_queries = [
        "list_tables",
        "stats"
    ]
    
    for query in test_queries:
        print(f"\n📝 Executing: {query}")
        result = await tool_manager.execute_tool(db_tool_name, query)
        
        if result.success:
            print(f"✅ Success")
            if query == "list_tables":
                tables = result.data.get("tables", [])
                print(f"   Found {len(tables)} tables: {tables}")
            elif query == "stats":
                if use_mysql:
                    total_records = result.data.get("total_records", 0)
                    total_tables = result.data.get("total_tables", 0)
                    print(f"   Database: {result.data.get('database')}")
                    print(f"   Tables: {total_tables}, Records: {total_records}")
                else:
                    print(f"   In-memory database stats: {result.data}")
        else:
            print(f"❌ Error: {result.error}")
    
    # If MySQL and tables exist, show more operations
    if use_mysql:
        tables_result = await tool_manager.execute_tool(db_tool_name, "list_tables")
        if tables_result.success and tables_result.data.get("tables"):
            tables = tables_result.data["tables"]
            
            if tables:
                first_table = tables[0]
                print(f"\n🔍 Advanced operations on table: {first_table}")
                
                # Describe table
                desc_result = await tool_manager.execute_tool(db_tool_name, f"describe {first_table}")
                if desc_result.success:
                    schema = desc_result.data
                    print(f"✅ Table schema:")
                    print(f"   Columns: {schema.get('columns', [])}")
                    print(f"   Primary Keys: {schema.get('primary_keys', [])}")
                
                # Get sample records
                get_result = await tool_manager.execute_tool(db_tool_name, f"get {first_table} * 3")
                if get_result.success:
                    records = get_result.data.get("records", [])
                    print(f"✅ Sample records: {len(records)} found")
                
                # Search test
                search_result = await tool_manager.execute_tool(db_tool_name, "search test")
                if search_result.success:
                    total_results = search_result.data.get("total_results", 0)
                    print(f"✅ Search test: {total_results} results found")
    
    print(f"\n🎉 MySQL Database Integration Demo Complete!")


async def demo_database_switching():
    """Demonstrate switching between database types."""
    
    print("\n🔄 Database Switching Demo")
    print("=" * 30)
    
    # Start with in-memory database
    tool_manager = EnhancedToolManager(use_mysql=False)
    print(f"Initial: {tool_manager}")
    
    # Add some data to in-memory database
    db_tool_name = tool_manager.get_database_tool_name()
    await tool_manager.execute_tool(db_tool_name, "list_tables")
    
    print(f"✅ In-memory database ready with sample data")
    
    # Try to switch to MySQL
    mysql_config = MySQLConfig.get_config()
    if MySQLConfig.validate_config(mysql_config):
        print(f"\n🔄 Switching to MySQL database...")
        tool_manager.switch_database_type(use_mysql=True, mysql_config=mysql_config)
        
        new_status = tool_manager.get_database_status()
        print(f"✅ Switched to: {new_status}")
        
        # Test MySQL operations
        mysql_result = await tool_manager.execute_tool("mysql_database", "list_tables")
        if mysql_result.success:
            print(f"✅ MySQL operations working")
        
        # Switch back to in-memory
        print(f"\n🔄 Switching back to in-memory database...")
        tool_manager.switch_database_type(use_mysql=False)
        print(f"✅ Back to in-memory database")
        
    else:
        print(f"❌ Cannot switch to MySQL - invalid configuration")


async def demo_agent_with_mysql():
    """Demonstrate React Agent using MySQL database."""
    
    print("\n🤖 React Agent with MySQL Database Demo")
    print("=" * 45)
    
    mysql_config = MySQLConfig.get_config()
    use_mysql = MySQLConfig.validate_config(mysql_config)
    
    if not use_mysql:
        print("❌ MySQL not configured. Using in-memory database.")
    
    # Initialize tool manager
    tool_manager = EnhancedToolManager(use_mysql=use_mysql, mysql_config=mysql_config)
    
    # Note: This would require the ReactAgent to be updated to use EnhancedToolManager
    # For now, just show the concept
    
    print(f"🔧 Tool Manager configured: {tool_manager}")
    print(f"📊 Database Status: {tool_manager.get_database_status()}")
    
    # Show available tools
    tools = tool_manager.get_tool_descriptions()
    print(f"\n🛠️  Available Tools:")
    for name, description in tools.items():
        print(f"   {name}: {description}")
    
    # Example queries that agent could make
    example_queries = [
        ("Show me all tables in the database", f"{tool_manager.get_database_tool_name()}", "list_tables"),
        ("Get database statistics", f"{tool_manager.get_database_tool_name()}", "stats"),
        ("Search for users in the database", f"{tool_manager.get_database_tool_name()}", "search user"),
    ]
    
    print(f"\n📝 Example Agent Queries:")
    for user_query, tool_name, tool_query in example_queries:
        print(f"\n👤 User: {user_query}")
        print(f"🤖 Agent would use: {tool_name}.execute('{tool_query}')")
        
        # Actually execute to show results
        result = await tool_manager.execute_tool(tool_name, tool_query)
        if result.success:
            print(f"✅ Result available: {type(result.data).__name__}")
        else:
            print(f"❌ Error: {result.error}")


def show_mysql_setup_guide():
    """Show MySQL setup guide."""
    
    print("📚 MySQL Database Setup Guide")
    print("=" * 35)
    
    print("""
🔧 Prerequisites:
   1. MySQL Server installed and running
   2. Database created for the agent
   3. User with appropriate permissions

🛠️  Installation:
   pip install mysql-connector-python

🔐 Configuration (Environment Variables):
   export MYSQL_HOST=localhost
   export MYSQL_PORT=3306
   export MYSQL_DATABASE=react_agent_db
   export MYSQL_USER=your_username
   export MYSQL_PASSWORD=your_password

📝 Create Database (SQL):
   CREATE DATABASE react_agent_db;
   CREATE USER 'agent_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON react_agent_db.* TO 'agent_user'@'localhost';
   FLUSH PRIVILEGES;

🧪 Test Connection:
   python test_mysql_database.py

🚀 Use with Agent:
   tool_manager = EnhancedToolManager(use_mysql=True)
   
💡 Features:
   ✅ Works with any existing MySQL database
   ✅ Automatically discovers all tables
   ✅ Supports full CRUD operations
   ✅ Intelligent search across tables
   ✅ Schema introspection
   ✅ Safe SQL execution with parameter binding
   ✅ Connection pooling and error handling
    """)


async def main():
    """Main function to run demos."""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            show_mysql_setup_guide()
        elif sys.argv[1] == "--switch":
            await demo_database_switching()
        elif sys.argv[1] == "--agent":
            await demo_agent_with_mysql()
        else:
            print("Usage: python mysql_database_example.py [--setup|--switch|--agent]")
    else:
        await demo_mysql_database_integration()


if __name__ == "__main__":
    asyncio.run(main())