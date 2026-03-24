
"""
File: config/init_database.py

Module Description:
    Script to initialize the SQLite database for the OT Video Management System.
    
    This script:
    1. Creates the database file if it doesn't exist
    2. Reads and executes the SQL schema from database_schema.sql
    3. Verifies that all tables were created correctly
    4. Reports any errors encountered
    
    This script should be run:
    - During initial setup (Day 10 of setup guide)
    - After any schema changes (to recreate database)
    - When database file is corrupted (to rebuild)
    
    The script is idempotent - it can be run multiple times safely.
    Tables use "IF NOT EXISTS" so running again won't lose data.

Dependencies:
    - sqlite3: Python's built-in SQLite interface
    - config.app_config: Application configuration

Usage:
    Command line:
        python3 config/init_database.py
    
    From Python:
        >>> from config.init_database import initialize_database
        >>> success = initialize_database()
        >>> if success:
        ...     print("Database ready!")

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.app_config import DATABASE_PATH, DATABASE_DIR


# ============================================================================
# DATABASE INITIALIZATION FUNCTION
# ============================================================================
def initialize_database(database_path=None, schema_file=None):
    """
    Initialize the SQLite database with schema from SQL file.
    
    This function:
    1. Creates database directory if it doesn't exist
    2. Creates database file if it doesn't exist
    3. Reads SQL schema from file
    4. Executes all SQL statements to create tables and indexes
    5. Verifies tables were created
    6. Commits changes
    
    Args:
        database_path (str|Path, optional): Path to database file.
                                           Defaults to DATABASE_PATH from config.
        schema_file (str|Path, optional): Path to schema SQL file.
                                         Defaults to database_schema.sql in config dir.
    
    Returns:
        bool: True if initialization successful, False otherwise
    
    Raises:
        sqlite3.Error: If database operation fails
        FileNotFoundError: If schema file doesn't exist
        
    Example:
        >>> initialize_database()
        Initializing database at /mnt/videostore/database/otvideo.db
        ✓ Database directory exists
        ✓ Schema file loaded (5234 characters)
        ✓ SQL executed successfully
        ✓ Database initialized successfully
        ✓ Tables created: 5
        True
    """
    # ========================================================================
    # STEP 1: Setup paths
    # ========================================================================
    # Use default paths from config if not provided
    if database_path is None:
        database_path = DATABASE_PATH
    else:
        database_path = Path(database_path)
    
    if schema_file is None:
        # Schema file is in same directory as this script
        schema_file = Path(__file__).parent / "database_schema.sql"
    else:
        schema_file = Path(schema_file)
    
    print(f"Initializing database at: {database_path}")
    
    # ========================================================================
    # STEP 2: Create database directory if needed
    # ========================================================================
    try:
        # Create parent directories with parents=True
        database_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"✓ Database directory exists: {database_path.parent}")
    except Exception as e:
        print(f"✗ Error creating database directory: {e}")
        return False
    
    # ========================================================================
    # STEP 3: Read SQL schema file
    # ========================================================================
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print(f"✓ Schema file loaded: {len(schema_sql)} characters")
        
        if len(schema_sql) == 0:
            print("✗ Error: Schema file is empty")
            return False
            
    except FileNotFoundError:
        print(f"✗ Error: Schema file not found: {schema_file}")
        return False
    except Exception as e:
        print(f"✗ Error reading schema file: {e}")
        return False
    
    # ========================================================================
    # STEP 4: Connect to database and execute schema
    # ========================================================================
    connection = None
    try:
        # Connect to database (creates file if it doesn't exist)
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()
        
        print("✓ Database connection established")
        
        # Execute schema SQL
        # executescript() allows multiple statements separated by semicolons
        cursor.executescript(schema_sql)
        
        print("✓ SQL schema executed successfully")
        
        # Commit changes to database file
        connection.commit()
        
        print("✓ Database initialized successfully")
        
    except sqlite3.Error as e:
        print(f"✗ SQLite error: {e}")
        if connection:
            connection.rollback()
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if connection:
            connection.rollback()
        return False
    
    # ========================================================================
    # STEP 5: Verify tables were created
    # ========================================================================
    try:
        # Query to get list of all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = cursor.fetchall()
        
        # Display tables
        print(f"✓ Tables created: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Expected tables
        expected_tables = {
            'recordings',
            'tags',
            'recording_tags',
            'export_log',
            'system_log',
            'schema_version'
        }
        
        # Check if all expected tables exist
        actual_tables = {table[0] for table in tables}
        missing_tables = expected_tables - actual_tables
        
        if missing_tables:
            print(f"⚠ Warning: Missing tables: {missing_tables}")
        else:
            print("✓ All expected tables created")
        
        # Get schema version
        cursor.execute("SELECT version, description FROM schema_version;")
        version = cursor.fetchone()
        if version:
            print(f"✓ Schema version: {version[0]} ({version[1]})")
        
    except sqlite3.Error as e:
        print(f"⚠ Warning: Could not verify tables: {e}")
        # Don't return False - database might still be functional
    
    finally:
        # Always close connection
        if connection:
            connection.close()
            print("✓ Database connection closed")
    
    # ========================================================================
    # STEP 6: Return success
    # ========================================================================
    return True


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def check_database_exists(database_path=None):
    """
    Check if database file exists and is accessible.
    
    Args:
        database_path (str|Path, optional): Path to database file.
                                           Defaults to DATABASE_PATH from config.
    
    Returns:
        bool: True if database exists and is accessible, False otherwise
    
    Example:
        >>> if not check_database_exists():
        ...     print("Database needs initialization")
    """
    if database_path is None:
        database_path = DATABASE_PATH
    else:
        database_path = Path(database_path)
    
    if not database_path.exists():
        return False
    
    # Try to connect to verify it's a valid database
    try:
        conn = sqlite3.connect(database_path)
        conn.execute("SELECT 1")  # Simple query to test connection
        conn.close()
        return True
    except:
        return False


def get_table_count(database_path=None):
    """
    Get count of records in each table.
    
    Args:
        database_path (str|Path, optional): Path to database file.
    
    Returns:
        dict: Dictionary with table names as keys and record counts as values
    
    Example:
        >>> counts = get_table_count()
        >>> print(f"Recordings: {counts['recordings']}")
        Recordings: 0
    """
    if database_path is None:
        database_path = DATABASE_PATH
    
    counts = {}
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = cursor.fetchall()
        
        # Count records in each table
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence':  # Skip internal table
                continue
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            counts[table_name] = count
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Error getting table counts: {e}")
    
    return counts


def reset_database(database_path=None):
    """
    Delete and recreate database (WARNING: DATA LOSS).
    
    This completely removes the database file and creates a fresh one.
    Use only when you want to start completely fresh.
    
    Args:
        database_path (str|Path, optional): Path to database file.
    
    Returns:
        bool: True if reset successful, False otherwise
    
    Warning:
        THIS DELETES ALL DATA! Use with caution!
    
    Example:
        >>> if input("Really delete all data? (yes/no): ") == "yes":
        ...     reset_database()
    """
    if database_path is None:
        database_path = DATABASE_PATH
    else:
        database_path = Path(database_path)
    
    print(f"⚠ WARNING: This will delete all data in {database_path}")
    
    # Delete database file if it exists
    if database_path.exists():
        try:
            database_path.unlink()
            print(f"✓ Deleted existing database file")
        except Exception as e:
            print(f"✗ Error deleting database file: {e}")
            return False
    
    # Reinitialize
    return initialize_database(database_path)


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    """
    Run database initialization when script is executed directly.
    
    Usage:
        python3 config/init_database.py
    
    Options can be added here for command-line arguments if needed.
    """
    print("=" * 70)
    print("OT Video Management System - Database Initialization")
    print("=" * 70)
    print()
    
    # Check if database already exists
    if check_database_exists():
        print(f"⚠ Database already exists at: {DATABASE_PATH}")
        print()
        
        # Show current table counts
        counts = get_table_count()
        print("Current database contents:")
        for table, count in counts.items():
            print(f"  {table:20s}: {count:6d} records")
        print()
        
        # Ask if user wants to continue
        response = input("Continue and update schema? (yes/no): ").strip().lower()
        if response != "yes":
            print("Aborted.")
            sys.exit(0)
        print()
    
    # Initialize database
    success = initialize_database()
    
    print()
    print("=" * 70)
    
    if success:
        print("✓ Database initialization completed successfully!")
        print()
        print(f"Database location: {DATABASE_PATH}")
        print()
        print("You can now run the application.")
        sys.exit(0)
    else:
        print("✗ Database initialization failed!")
        print()
        print("Please check the error messages above and fix any issues.")
        sys.exit(1)
