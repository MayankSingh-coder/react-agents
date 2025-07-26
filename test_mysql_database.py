#!/usr/bin/env python3
"""Test script for MySQL Database Tool."""

import asyncio
import sys
import json
from mysql_config import MySQLConfig
from tools.mysql_database_tool import MySQLDatabaseTool


async def test_mysql_database_tool():
    """Test the MySQL database tool functionality."""
    
    print("🚀 Testing MySQL Database Tool")
    print("=" * 50)
    
    # Get configuration
    config = MySQLConfig.get_config()
    MySQLConfig.print_config(config)
    
    if not MySQLConfig.validate_config(config):
        print("❌ Invalid configuration. Please check your settings.")
        return False
    
    try:
        # Initialize the MySQL database tool
        print("\n🔌 Connecting to MySQL database...")
        db_tool = MySQLDatabaseTool(
            host=config["host"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            port=config["port"]
        )
        print("✅ Successfully connected to MySQL database")
        
        # Test operations
        test_queries = [
            ("list_tables", "📋 List all tables in database"),
            ("stats", "📊 Get database statistics"),
        ]
        
        # Execute basic tests
        for query, description in test_queries:
            print(f"\n{description}")
            print(f"Query: {query}")
            
            result = await db_tool.execute(query)
            
            if result.success:
                print("✅ Success")
                if query == "list_tables":
                    tables = result.data.get("tables", [])
                    print(f"   Found {len(tables)} tables: {tables}")
                elif query == "stats":
                    stats = result.data
                    print(f"   Database: {stats.get('database')}")
                    print(f"   Total tables: {stats.get('total_tables')}")
                    print(f"   Total records: {stats.get('total_records')}")
            else:
                print(f"❌ Error: {result.error}")
        
        # Interactive mode if tables exist
        tables_result = await db_tool.execute("list_tables")
        if tables_result.success and tables_result.data.get("tables"):
            tables = tables_result.data["tables"]
            
            print(f"\n🔍 Testing operations on existing tables...")
            
            # Test describe on first table
            first_table = tables[0]
            print(f"\n📖 Describing table: {first_table}")
            describe_result = await db_tool.execute(f"describe {first_table}")
            
            if describe_result.success:
                schema = describe_result.data
                print(f"✅ Table schema retrieved")
                print(f"   Columns: {schema.get('columns', [])}")
                print(f"   Primary keys: {schema.get('primary_keys', [])}")
            else:
                print(f"❌ Error describing table: {describe_result.error}")
            
            # Test get operation on first table (limited)
            print(f"\n📄 Getting sample records from: {first_table}")
            get_result = await db_tool.execute(f"get {first_table} * 5")
            
            if get_result.success:
                records = get_result.data.get("records", [])
                print(f"✅ Retrieved {len(records)} records")
                if records:
                    print(f"   Sample record keys: {list(records[0].keys())}")
            else:
                print(f"❌ Error getting records: {get_result.error}")
            
            # Test search functionality
            print(f"\n🔍 Testing search functionality...")
            search_result = await db_tool.execute("search test")
            
            if search_result.success:
                search_data = search_result.data
                total_results = search_data.get("total_results", 0)
                tables_with_results = search_data.get("tables_searched", [])
                print(f"✅ Search completed")
                print(f"   Total results: {total_results}")
                print(f"   Tables with results: {tables_with_results}")
            else:
                print(f"❌ Search error: {search_result.error}")
        
        print(f"\n🎉 MySQL Database Tool testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False


async def interactive_mysql_demo():
    """Interactive demo of MySQL database tool."""
    
    print("\n🎮 Interactive MySQL Database Demo")
    print("=" * 40)
    print("Enter MySQL queries or 'help' for examples, 'quit' to exit")
    
    # Get configuration
    config = MySQLConfig.get_config()
    
    try:
        db_tool = MySQLDatabaseTool(
            host=config["host"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            port=config["port"]
        )
        
        help_text = """
📖 Available Commands:
   list_tables                          - List all tables
   describe <table>                     - Get table schema
   get <table>                          - Get all records (limited to 100)
   get <table> * 10                     - Get 10 records
   get <table> id=123                   - Get record with condition
   search <term>                        - Search across all tables
   stats                                - Database statistics
   sql SELECT * FROM table LIMIT 5      - Custom SQL query
   
📝 Examples:
   get users
   describe products
   search john@email.com
   sql SELECT COUNT(*) FROM orders
        """
        
        while True:
            try:
                query = input("\n> ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                elif query.lower() in ['help', 'h']:
                    print(help_text)
                    continue
                elif not query:
                    continue
                
                print(f"Executing: {query}")
                result = await db_tool.execute(query)
                
                if result.success:
                    print("✅ Success")
                    
                    # Pretty print results based on operation
                    if isinstance(result.data, dict):
                        if "records" in result.data:
                            records = result.data["records"]
                            print(f"📄 Found {len(records)} records")
                            if records and len(records) <= 10:
                                print(json.dumps(records, indent=2, default=str))
                            elif records:
                                print("Sample record:")
                                print(json.dumps(records[0], indent=2, default=str))
                        elif "tables" in result.data:
                            tables = result.data["tables"]
                            print(f"📋 Tables: {tables}")
                        else:
                            print(json.dumps(result.data, indent=2, default=str))
                    else:
                        print(f"Result: {result.data}")
                        
                else:
                    print(f"❌ Error: {result.error}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                
    except Exception as e:
        print(f"❌ Failed to initialize database tool: {str(e)}")
        return


def show_setup_instructions():
    """Show setup instructions for MySQL."""
    
    print("🛠️  MySQL Database Tool Setup")
    print("=" * 35)
    
    print("\n1️⃣  Install MySQL connector:")
    print("   pip install mysql-connector-python")
    
    print("\n2️⃣  Configure database connection:")
    print("   Set environment variables or update mysql_config.py")
    
    print("\n3️⃣  Required environment variables:")
    print("   MYSQL_HOST=your_host")
    print("   MYSQL_DATABASE=your_database") 
    print("   MYSQL_USER=your_username")
    print("   MYSQL_PASSWORD=your_password")
    print("   MYSQL_PORT=3306")
    
    print("\n4️⃣  Test connection:")
    print("   python test_mysql_database.py")
    
    print("\n5️⃣  Start interactive demo:")
    print("   python test_mysql_database.py --interactive")


async def main():
    """Main function to run tests or interactive demo."""
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--interactive', '-i']:
        await interactive_mysql_demo()
    elif len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_setup_instructions()
    else:
        success = await test_mysql_database_tool()
        if success:
            print("\n🎮 Run with --interactive flag for interactive demo")
            print("🛠️  Run with --help flag for setup instructions")


if __name__ == "__main__":
    asyncio.run(main())