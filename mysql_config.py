"""MySQL Database Configuration for React Agent Service."""

import os
from typing import Dict, Any

class MySQLConfig:
    """MySQL database configuration management."""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get MySQL configuration from environment variables or defaults."""
        return {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "database": os.getenv("MYSQL_DATABASE", "react_agent_db"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "password")
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Validate MySQL configuration."""
        required_fields = ["host", "database", "user", "password"]
        
        for field in required_fields:
            if not config.get(field):
                print(f"❌ Missing required MySQL config: {field}")
                return False
        
        if not isinstance(config.get("port"), int):
            print("❌ MySQL port must be an integer")
            return False
        
        return True
    
    @staticmethod
    def print_config(config: Dict[str, Any]):
        """Print MySQL configuration (without password)."""
        safe_config = config.copy()
        safe_config["password"] = "***" if config.get("password") else None
        
        print("🔧 MySQL Configuration:")
        for key, value in safe_config.items():
            print(f"   {key}: {value}")

# Example usage and setup instructions
def setup_mysql_environment():
    """Show setup instructions for MySQL environment."""
    
    print("🚀 MySQL Database Tool Setup Instructions")
    print("=" * 50)
    print()
    print("1. Install MySQL connector:")
    print("   pip install mysql-connector-python")
    print()
    print("2. Set environment variables (recommended):")
    print("   export MYSQL_HOST=localhost")
    print("   export MYSQL_PORT=3306")
    print("   export MYSQL_DATABASE=your_database_name")
    print("   export MYSQL_USER=your_username")
    print("   export MYSQL_PASSWORD=your_password")
    print()
    print("3. Or create a .env file:")
    print("   MYSQL_HOST=localhost")
    print("   MYSQL_PORT=3306")
    print("   MYSQL_DATABASE=your_database_name")
    print("   MYSQL_USER=your_username")
    print("   MYSQL_PASSWORD=your_password")
    print()
    print("4. Test connection with test script")
    print()

if __name__ == "__main__":
    setup_mysql_environment()
    
    print("📋 Current Configuration:")
    config = MySQLConfig.get_config()
    MySQLConfig.print_config(config)
    
    if MySQLConfig.validate_config(config):
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has issues")