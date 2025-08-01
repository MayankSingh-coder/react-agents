"""
MySQL Database Security Configuration Template

Copy the relevant configuration section to your config.py file
and modify the permissions according to your security requirements.
"""

# =============================================================================
# MYSQL SECURITY CONFIGURATION OPTIONS
# =============================================================================

# Option 1: COMPLETE READ-ONLY MODE (Recommended for production)
# Only allows search, select, describe, list operations
MYSQL_READ_ONLY_MODE = True
MYSQL_OPERATIONS = {
    # Read operations (safe)
    "allow_select": True,           # SELECT queries ✅
    "allow_search": True,           # SEARCH operations ✅
    "allow_describe": True,         # DESCRIBE/SHOW table structure ✅
    "allow_list_tables": True,      # LIST_TABLES operation ✅
    "allow_stats": True,            # Database statistics ✅
    "allow_help": True,             # Help operation ✅
    
    # Write operations (disabled for security)
    "allow_insert": False,          # INSERT/SET operations ❌
    "allow_update": False,          # UPDATE operations ❌
    "allow_delete": False,          # DELETE operations ❌
    
    # Schema operations (disabled for security)
    "allow_create_table": False,    # CREATE TABLE operations ❌
    "allow_drop_table": False,      # DROP TABLE operations ❌
    "allow_alter_table": False,     # ALTER TABLE operations ❌
    
    # Advanced operations (disabled for security)
    "allow_custom_sql": False,      # Custom SQL queries ❌
    "allow_dangerous_operations": False,  # DROP, TRUNCATE, etc. ❌
}

# =============================================================================

# Option 2: LIMITED WRITE MODE (Allow specific data operations)
# Allows data insertion and updates but no schema changes
"""
MYSQL_READ_ONLY_MODE = False
MYSQL_OPERATIONS = {
    # Read operations
    "allow_select": True,
    "allow_search": True,
    "allow_describe": True,
    "allow_list_tables": True,
    "allow_stats": True,
    "allow_help": True,
    
    # Data write operations (enabled)
    "allow_insert": True,           # INSERT/SET operations ✅
    "allow_update": True,           # UPDATE operations ✅
    "allow_delete": False,          # DELETE operations ❌ (still restricted)
    
    # Schema operations (disabled for security)
    "allow_create_table": False,
    "allow_drop_table": False,
    "allow_alter_table": False,
    
    # Advanced operations (disabled)
    "allow_custom_sql": False,
    "allow_dangerous_operations": False,
}
"""

# =============================================================================

# Option 3: DEVELOPMENT MODE (Full access - use with caution)
# Allows all operations - only for development environments
"""
MYSQL_READ_ONLY_MODE = False
MYSQL_OPERATIONS = {
    # Read operations
    "allow_select": True,
    "allow_search": True,
    "allow_describe": True,
    "allow_list_tables": True,
    "allow_stats": True,
    "allow_help": True,
    
    # Write operations
    "allow_insert": True,
    "allow_update": True,
    "allow_delete": True,
    
    # Schema operations
    "allow_create_table": True,
    "allow_drop_table": False,      # Still keep some restrictions
    "allow_alter_table": False,
    
    # Advanced operations
    "allow_custom_sql": True,       # Allow custom SQL
    "allow_dangerous_operations": False,  # Keep dangerous ops disabled
}
"""

# =============================================================================

# Option 4: CUSTOM CONFIGURATION
# Define your own permission set based on specific requirements
"""
MYSQL_READ_ONLY_MODE = False
MYSQL_OPERATIONS = {
    # Customize based on your needs
    "allow_select": True,           # Always recommended
    "allow_search": True,           # Always recommended
    "allow_describe": True,         # Always recommended
    "allow_list_tables": True,      # Always recommended
    "allow_stats": True,            # Always recommended
    "allow_help": True,             # Always recommended
    
    # Enable only the write operations you need
    "allow_insert": False,          # Set to True if needed
    "allow_update": False,          # Set to True if needed
    "allow_delete": False,          # Set to True if needed
    
    # Schema operations - enable carefully
    "allow_create_table": False,    # Set to True if needed
    "allow_drop_table": False,      # Usually keep False
    "allow_alter_table": False,     # Usually keep False
    
    # Advanced operations - enable very carefully
    "allow_custom_sql": False,      # Allows raw SQL execution
    "allow_dangerous_operations": False,  # Keep False for safety
}
"""

# =============================================================================
# SECURITY NOTES
# =============================================================================

"""
🔒 SECURITY BEST PRACTICES:

1. READ-ONLY MODE (Option 1) - Recommended for:
   - Production environments
   - Public-facing applications
   - When you only need to query data

2. LIMITED WRITE MODE (Option 2) - Suitable for:
   - Applications that need to insert/update data
   - Controlled environments with trusted users
   - When schema changes are managed separately

3. DEVELOPMENT MODE (Option 3) - Only for:
   - Local development
   - Testing environments
   - Non-production systems

4. CUSTOM CONFIGURATION (Option 4) - When you need:
   - Specific permission combinations
   - Fine-grained control
   - Compliance with security policies

⚠️  WARNINGS:
- Never enable 'allow_dangerous_operations' in production
- Be careful with 'allow_custom_sql' as it allows raw SQL execution
- 'allow_drop_table' can cause data loss
- Always test configuration changes in development first

🛡️  ADDITIONAL SECURITY MEASURES:
- Use database user accounts with minimal required privileges
- Enable MySQL audit logging
- Implement application-level access controls
- Regular security audits of database permissions
- Use encrypted connections (SSL/TLS)
"""

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================

"""
📝 HOW TO USE THIS TEMPLATE:

1. Choose one of the configuration options above (Option 1-4)
2. Copy the MYSQL_READ_ONLY_MODE and MYSQL_OPERATIONS to your config.py
3. Modify permissions as needed for your use case
4. Test the configuration using demo_mysql_security_config.py
5. Deploy to your environment

🧪 TESTING YOUR CONFIGURATION:
Run the demo script to verify your configuration works as expected:
    python demo_mysql_security_config.py

🔄 CHANGING CONFIGURATION:
1. Edit config.py with new settings
2. Restart your application
3. Verify changes with the demo script

🆘 TROUBLESHOOTING:
- If operations fail unexpectedly, check the permission settings
- Use 'mysql_database help' command to see available operations
- Check application logs for permission denied messages
- Verify MySQL connection and credentials
"""