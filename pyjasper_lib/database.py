"""
Database connection and query execution functionality.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse
from .exceptions import DatabaseError


class DatabaseEngine:
    """Database engine for executing queries across different database types."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db_type = self._detect_db_type()
        self.connection = None
    
    def _detect_db_type(self) -> str:
        """Detect database type from connection string."""
        if self.connection_string.startswith('sqlite:///'):
            return 'sqlite'
        elif self.connection_string.startswith('mysql://'):
            return 'mysql'
        elif self.connection_string.startswith('postgresql://'):
            return 'postgresql'
        else:
            raise DatabaseError(f"Unsupported database type in connection string: {self.connection_string}")
    
    def connect(self):
        """Establish database connection."""
        try:
            if self.db_type == 'sqlite':
                db_path = self.connection_string.replace('sqlite:///', '')
                if not os.path.exists(db_path):
                    raise DatabaseError(f"SQLite database file not found: {db_path}")
                self.connection = sqlite3.connect(db_path)
                self.connection.row_factory = sqlite3.Row  # Enable column access by name
            
            elif self.db_type == 'mysql':
                try:
                    import mysql.connector
                    parsed = urlparse(self.connection_string)
                    self.connection = mysql.connector.connect(
                        host=parsed.hostname,
                        port=parsed.port or 3306,
                        user=parsed.username,
                        password=parsed.password,
                        database=parsed.path.lstrip('/')
                    )
                except ImportError:
                    raise DatabaseError("mysql-connector-python package required for MySQL connections")
            
            elif self.db_type == 'postgresql':
                try:
                    import psycopg2
                    import psycopg2.extras
                    self.connection = psycopg2.connect(
                        self.connection_string.replace('postgresql://', 'postgres://')
                    )
                except ImportError:
                    raise DatabaseError("psycopg2 package required for PostgreSQL connections")
            
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            if self.db_type == 'sqlite':
                if parameters:
                    # Convert named parameters for SQLite
                    sqlite_params = {f":{k}": v for k, v in parameters.items()}
                    cursor.execute(query, sqlite_params)
                else:
                    cursor.execute(query)
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i] if i < len(row) else None
                    result.append(row_dict)
                
                return result
            
            elif self.db_type == 'mysql':
                cursor.execute(query, parameters or {})
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i] if i < len(row) else None
                    result.append(row_dict)
                
                return result
            
            elif self.db_type == 'postgresql':
                import psycopg2.extras
                cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute(query, parameters or {})
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    result.append(dict(row))
                
                return result
                
        except Exception as e:
            raise DatabaseError(f"Query execution failed: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a table."""
        if not self.connection:
            self.connect()
        
        try:
            if self.db_type == 'sqlite':
                cursor = self.connection.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema = []
                for col in columns:
                    schema.append({
                        'name': col[1],
                        'type': col[2],
                        'nullable': not col[3],
                        'default': col[4],
                        'primary_key': bool(col[5])
                    })
                
                return schema
            
            elif self.db_type == 'mysql':
                cursor = self.connection.cursor()
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                schema = []
                for col in columns:
                    schema.append({
                        'name': col[0],
                        'type': col[1],
                        'nullable': col[2] == 'YES',
                        'default': col[4],
                        'primary_key': col[3] == 'PRI'
                    })
                
                return schema
            
            elif self.db_type == 'postgresql':
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                
                schema = []
                for col in columns:
                    schema.append({
                        'name': col[0],
                        'type': col[1],
                        'nullable': col[2] == 'YES',
                        'default': col[3],
                        'primary_key': False  # Would need additional query for PK info
                    })
                
                return schema
                
        except Exception as e:
            raise DatabaseError(f"Failed to get table schema: {e}")
    
    def get_tables(self) -> List[str]:
        """Get list of tables in the database."""
        if not self.connection:
            self.connect()
        
        try:
            if self.db_type == 'sqlite':
                cursor = self.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
            
            elif self.db_type == 'mysql':
                cursor = self.connection.cursor()
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
            
            elif self.db_type == 'postgresql':
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                return tables
                
        except Exception as e:
            raise DatabaseError(f"Failed to get table list: {e}")
    
    def test_connection(self) -> bool:
        """Test if the database connection is working."""
        try:
            self.connect()
            
            if self.db_type == 'sqlite':
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
            elif self.db_type == 'mysql':
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
            elif self.db_type == 'postgresql':
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
            
            return True
        except Exception:
            return False
        finally:
            self.disconnect()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class DataProcessor:
    """Processes data for report generation including grouping and aggregations."""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
    
    def group_by(self, field: str) -> Dict[Any, List[Dict[str, Any]]]:
        """Group data by a field."""
        groups = {}
        for row in self.data:
            key = row.get(field)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        return groups
    
    def calculate_sum(self, field: str, group_data: List[Dict[str, Any]] = None) -> float:
        """Calculate sum of a numeric field."""
        data_to_process = group_data if group_data is not None else self.data
        total = 0.0
        for row in data_to_process:
            value = row.get(field, 0)
            if isinstance(value, (int, float)):
                total += value
            elif isinstance(value, str):
                try:
                    total += float(value)
                except ValueError:
                    pass
        return total
    
    def calculate_average(self, field: str, group_data: List[Dict[str, Any]] = None) -> float:
        """Calculate average of a numeric field."""
        data_to_process = group_data if group_data is not None else self.data
        if not data_to_process:
            return 0.0
        
        total = self.calculate_sum(field, data_to_process)
        return total / len(data_to_process)
    
    def calculate_count(self, group_data: List[Dict[str, Any]] = None) -> int:
        """Calculate count of rows."""
        data_to_process = group_data if group_data is not None else self.data
        return len(data_to_process)
    
    def calculate_min(self, field: str, group_data: List[Dict[str, Any]] = None) -> Any:
        """Calculate minimum value of a field."""
        data_to_process = group_data if group_data is not None else self.data
        if not data_to_process:
            return None
        
        values = [row.get(field) for row in data_to_process if row.get(field) is not None]
        return min(values) if values else None
    
    def calculate_max(self, field: str, group_data: List[Dict[str, Any]] = None) -> Any:
        """Calculate maximum value of a field."""
        data_to_process = group_data if group_data is not None else self.data
        if not data_to_process:
            return None
        
        values = [row.get(field) for row in data_to_process if row.get(field) is not None]
        return max(values) if values else None
    
    def sort_by(self, fields: Union[str, List[str]], ascending: bool = True) -> List[Dict[str, Any]]:
        """Sort data by one or more fields."""
        if isinstance(fields, str):
            fields = [fields]
        
        def sort_key(row):
            return tuple(row.get(field, '') for field in fields)
        
        return sorted(self.data, key=sort_key, reverse=not ascending)
    
    def filter_data(self, condition: callable) -> List[Dict[str, Any]]:
        """Filter data based on a condition function."""
        return [row for row in self.data if condition(row)]