# MySQL Database Tool for React Agent

## 🚀 Overview

The MySQL Database Tool extends the React Agent's capabilities by connecting to real MySQL databases instead of just using in-memory storage. This allows the agent to:

- 🔍 **Work with any existing MySQL database**
- 📊 **Automatically discover all tables and schemas**
- 🛠️ **Perform full CRUD operations on real data**
- 🔍 **Intelligent search across all tables**
- 📈 **Get comprehensive database statistics**
- 🔒 **Safe SQL execution with parameter binding**

## 📋 Features

### ✅ **Dynamic Table Discovery**
- Automatically discovers all tables in your database
- No need to predefine table structures
- Works with any MySQL database schema

### ✅ **Full CRUD Operations**
```bash
# Create/Insert
set users {"name": "John Doe", "email": "john@example.com"}

# Read/Query
get users                    # Get all users
get users id=123            # Get specific user
get users * 10              # Get 10 users

# Update
update users {"name": "Jane Doe"} where id=123

# Delete
delete users where id=123
```

### ✅ **Intelligent Search**
```bash
search john@email.com        # Search across all tables
search users department      # Search specific table context
```

### ✅ **Schema Introspection**
```bash
describe users              # Get table schema
list_tables                # List all tables
stats                      # Database statistics
```

### ✅ **Custom SQL Support**
```bash
sql SELECT COUNT(*) FROM orders WHERE status='pending'
sql SELECT u.name, o.total FROM users u JOIN orders o ON u.id=o.user_id
```

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install mysql-connector-python
```

### 2. Configure Database Connection

**Option A: Environment Variables (Recommended)**
```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=your_database_name
export MYSQL_USER=your_username
export MYSQL_PASSWORD=your_password
```

**Option B: .env File**
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
```

**Option C: Direct Configuration**
```python
mysql_config = {
    "host": "localhost",
    "port": 3306,
    "database": "your_database",
    "user": "your_username", 
    "password": "your_password"
}
```

### 3. Database Setup (MySQL)
```sql
-- Create database
CREATE DATABASE react_agent_db;

-- Create user with permissions
CREATE USER 'agent_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON react_agent_db.* TO 'agent_user'@'localhost';
FLUSH PRIVILEGES;
```

## 🎯 Usage Examples

### Basic Integration
```python
from tools.enhanced_tool_manager import EnhancedToolManager
from mysql_config import MySQLConfig

# Initialize with MySQL
config = MySQLConfig.get_config()
tool_manager = EnhancedToolManager(use_mysql=True, mysql_config=config)

# Use with agent
result = await tool_manager.execute_tool("mysql_database", "list_tables")
```

### Command Examples

#### **Table Management**
```bash
list_tables                          # List all tables in database
describe users                       # Get table schema and column info
stats                               # Comprehensive database statistics
```

#### **Data Operations**
```bash
# Insert new record
set products {"name": "Laptop", "price": 999.99, "category": "electronics"}

# Query data
get products                         # Get all products (limited to 100)
get products * 50                    # Get 50 products
get products id=123                  # Get specific product
get products price > 500             # Get expensive products

# Update records
update products {"price": 899.99} where id=123

# Delete records  
delete products where category='discontinued'
```

#### **Search Operations**
```bash
search laptop                        # Search "laptop" across all tables
search orders pending                # Search "pending" in orders context
search @gmail.com                    # Find all Gmail addresses
```

#### **Custom SQL**
```bash
sql SELECT * FROM users WHERE created_at > '2024-01-01'
sql SELECT COUNT(*) FROM orders GROUP BY status
```

## 🔧 Advanced Configuration

### Enhanced Tool Manager
```python
from tools.enhanced_tool_manager import EnhancedToolManager

# Initialize with MySQL
tool_manager = EnhancedToolManager(use_mysql=True)

# Check database status
status = tool_manager.get_database_status()
print(f"Database Type: {status['type']}")
print(f"Connected: {status.get('connected', False)}")

# Switch database types dynamically
tool_manager.switch_database_type(use_mysql=False)  # Switch to in-memory
tool_manager.switch_database_type(use_mysql=True)   # Switch back to MySQL
```

### Connection Management
```python
from tools.mysql_database_tool import MySQLDatabaseTool

# Direct tool usage
db_tool = MySQLDatabaseTool(
    host="localhost",
    database="myapp_db", 
    user="myuser",
    password="mypass"
)

# Execute operations
result = await db_tool.execute("get users")
```

## 🧪 Testing

### Test Database Connection
```bash
# Basic connection test
python test_mysql_database.py

# Interactive demo
python test_mysql_database.py --interactive

# Setup help
python test_mysql_database.py --help
```

### Integration Examples
```bash
# MySQL integration demo
python examples/mysql_database_example.py

# Database switching demo
python examples/mysql_database_example.py --switch

# Agent integration demo  
python examples/mysql_database_example.py --agent
```

## 🔒 Security Features

### ✅ **SQL Injection Prevention**
- All queries use parameter binding
- User input is properly escaped
- No direct string concatenation in SQL

### ✅ **Safe Operations**
- Dangerous operations (DROP, TRUNCATE) are blocked
- DELETE operations require WHERE clauses
- Query result limits to prevent memory issues

### ✅ **Connection Security**
- Connection pooling and proper cleanup
- Automatic reconnection handling
- Secure credential management via environment variables

## 📊 Schema Support

The tool automatically works with any MySQL table structure:

```sql
-- Example: E-commerce Database
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200),
    price DECIMAL(10,2),
    category VARCHAR(50),
    stock_quantity INT
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    total DECIMAL(10,2),
    status ENUM('pending', 'completed', 'cancelled'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Agent Operations:**
```bash
list_tables                    # → ['users', 'products', 'orders']
describe products              # → Shows columns, types, primary keys
get orders status='pending'    # → Gets pending orders
search laptop                  # → Searches across all tables
stats                          # → Shows record counts per table
```

## 🚨 Error Handling

The tool provides comprehensive error handling:

```python
result = await tool_manager.execute_tool("mysql_database", "invalid_query")

if result.success:
    data = result.data
else:
    print(f"Error: {result.error}")
    # Errors include:
    # - Connection failures
    # - Invalid SQL syntax
    # - Table not found
    # - Permission denied
    # - Data type mismatches
```

## 🔄 Migration from In-Memory Database

Existing agents can easily switch to MySQL:

```python
# Before (In-memory)
from agent.tool_manager import ToolManager
tool_manager = ToolManager()

# After (MySQL)
from tools.enhanced_tool_manager import EnhancedToolManager
tool_manager = EnhancedToolManager(use_mysql=True)

# Same interface, real database backend!
result = await tool_manager.execute_tool("mysql_database", "list_tables")
```

## 📈 Performance Considerations

- **Connection Pooling**: Reuses database connections
- **Schema Caching**: Caches table schemas for 5 minutes
- **Query Limits**: Default 100 record limit for safety
- **Index Usage**: Leverage your existing database indexes
- **Parameterized Queries**: Efficient query execution

## 🛡️ Best Practices

1. **Use Environment Variables** for database credentials
2. **Create Dedicated Database User** with limited permissions
3. **Regular Backups** before letting agents modify data
4. **Monitor Query Performance** in production
5. **Use WHERE clauses** for better performance
6. **Test with Sample Data** before production use

## 🎉 Benefits Over In-Memory Database

| Feature | In-Memory | MySQL |
|---------|-----------|--------|
| **Data Persistence** | ❌ Lost on restart | ✅ Permanent storage |
| **Data Volume** | ❌ Limited by RAM | ✅ Unlimited |
| **Multi-Agent Access** | ❌ Single instance | ✅ Shared across agents |
| **Existing Data** | ❌ Must recreate | ✅ Use existing databases |
| **Analytics** | ❌ Basic | ✅ Full SQL capabilities |
| **Backup/Recovery** | ❌ Manual | ✅ Standard database tools |
| **Performance** | ✅ Very fast | ✅ Good with indexes |
| **Setup Complexity** | ✅ None | ❌ Requires MySQL setup |

## 🔗 Integration with React Agent

The MySQL database tool seamlessly integrates with the React Agent architecture:

1. **Tool Discovery**: Agent automatically discovers all database tables
2. **Natural Language**: Agent can translate user requests to database operations
3. **Context Awareness**: Agent understands table relationships and data types
4. **Error Recovery**: Agent handles database errors gracefully
5. **Multi-Step Operations**: Agent can chain database operations

Example agent conversation:
```
User: "Show me all users who placed orders last month"
Agent: I'll search the database for that information.
      [Uses: sql SELECT u.* FROM users u JOIN orders o ON u.id=o.user_id WHERE o.created_at > '2024-01-01']
Result: Found 150 users who placed orders in January 2024.
```

This MySQL integration transforms your React Agent from a simple chatbot into a powerful database assistant! 🚀