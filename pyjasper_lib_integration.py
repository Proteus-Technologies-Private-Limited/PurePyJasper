"""
Integration module to use PyJasper library with the existing Flask application.
"""

from pyjasper_lib import JasperReport
from pyjasper_lib.exceptions import JasperError, JRXMLParseError, DatabaseError, RenderError
import logging

logger = logging.getLogger(__name__)


class PyJasperIntegration:
    """Integration class for using PyJasper library in the Flask app."""
    
    def __init__(self):
        """Initialize the integration."""
        pass
    
    def generate_report(self, jrxml_content: str, connection_string: str = None, 
                       output_format: str = 'html', parameters: dict = None) -> tuple:
        """
        Generate a report using the PyJasper library.
        
        Args:
            jrxml_content: JRXML content as string
            connection_string: Database connection string
            output_format: Output format ('html' or 'pdf')
            parameters: Report parameters
            
        Returns:
            Tuple of (content_bytes, error_message)
        """
        try:
            # Create report instance
            report = JasperReport(jrxml_content=jrxml_content)
            
            # Set database connection if provided
            if connection_string:
                report.set_database_connection(connection_string)
            
            # Set parameters if provided
            if parameters:
                report.set_parameters(parameters)
            
            # Generate report based on format
            if output_format.lower() == 'pdf':
                content = report.generate_pdf()
            else:
                content = report.generate_html()
                
            # Clean up any fallback messages from HTML content
            if output_format.lower() == 'html' and content:
                content_str = content.decode('utf-8') if isinstance(content, bytes) else str(content)
                
                # Remove any fallback notices or warnings
                import re
                content_str = re.sub(r'<div[^>]*fallback[^>]*>.*?</div>', '', content_str, flags=re.DOTALL | re.IGNORECASE)
                content_str = re.sub(r'<p[^>]*>.*?fallback.*?</p>', '', content_str, flags=re.DOTALL | re.IGNORECASE)
                content_str = re.sub(r'Note:.*?JasperReports.*?\.', '', content_str, flags=re.DOTALL | re.IGNORECASE)
                
                content = content_str.encode('utf-8')
            
            return content, None
            
        except JRXMLParseError as e:
            logger.error(f"JRXML parsing error: {e}")
            return None, f"JRXML parsing error: {str(e)}"
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return None, f"Database error: {str(e)}"
        except RenderError as e:
            logger.error(f"Rendering error: {e}")
            return None, f"Rendering error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None, f"Unexpected error: {str(e)}"
    
    def validate_jrxml(self, jrxml_content: str) -> dict:
        """
        Validate JRXML content.
        
        Args:
            jrxml_content: JRXML content to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            report = JasperReport(jrxml_content=jrxml_content)
            validation = report.validate_report()
            return {
                'valid': validation['valid'],
                'issues': validation['issues'],
                'warnings': validation['warnings'],
                'info': report.get_report_info()
            }
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'info': {}
            }
    
    def preview_data(self, jrxml_content: str, connection_string: str, limit: int = 10) -> tuple:
        """
        Preview data for a report.
        
        Args:
            jrxml_content: JRXML content
            connection_string: Database connection string
            limit: Maximum number of rows to return
            
        Returns:
            Tuple of (data_list, error_message)
        """
        try:
            report = JasperReport(jrxml_content=jrxml_content)
            
            if connection_string:
                report.set_database_connection(connection_string)
                data = report.preview_data(limit)
                return data, None
            else:
                return [], "No database connection provided"
                
        except Exception as e:
            logger.error(f"Data preview error: {e}")
            return [], f"Data preview error: {str(e)}"
    
    def get_database_schema(self, connection_string: str) -> tuple:
        """
        Get database schema information.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Tuple of (schema_dict, error_message)
        """
        try:
            from pyjasper_lib.database import DatabaseEngine
            
            engine = DatabaseEngine(connection_string)
            tables = engine.get_tables()
            
            schema_info = {
                'database_type': engine.db_type,
                'tables': []
            }
            
            for table in tables:
                try:
                    columns = engine.get_table_schema(table)
                    schema_info['tables'].append({
                        'name': table,
                        'columns': columns
                    })
                except Exception as e:
                    logger.warning(f"Failed to get schema for table {table}: {e}")
            
            return schema_info, None
            
        except Exception as e:
            logger.error(f"Schema retrieval error: {e}")
            return None, f"Schema retrieval error: {str(e)}"
    
    def generate_sample_jrxml(self, table_name: str, connection_string: str) -> tuple:
        """
        Generate sample JRXML based on a database table.
        
        Args:
            table_name: Name of the database table
            connection_string: Database connection string
            
        Returns:
            Tuple of (jrxml_content, error_message)
        """
        try:
            from pyjasper_lib.database import DatabaseEngine
            from pyjasper_lib.core import ReportBuilder
            
            engine = DatabaseEngine(connection_string)
            schema = engine.get_table_schema(table_name)
            
            # Create report builder
            builder = ReportBuilder(f"{table_name.title()} Report")
            builder.set_title(f"{table_name.replace('_', ' ').title()} Report")
            builder.set_query(f"SELECT * FROM {table_name}")
            
            # Add fields based on schema
            for column in schema:
                field_type = "java.lang.String"  # Default
                if 'int' in column['type'].lower():
                    field_type = "java.lang.Integer"
                elif 'real' in column['type'].lower() or 'decimal' in column['type'].lower():
                    field_type = "java.math.BigDecimal"
                elif 'date' in column['type'].lower():
                    field_type = "java.util.Date"
                
                builder.add_field(column['name'], field_type)
                builder.add_column_header(column['name'].replace('_', ' ').title(), 100)
            
            jrxml_content = builder.build_jrxml()
            return jrxml_content, None
            
        except Exception as e:
            logger.error(f"Sample JRXML generation error: {e}")
            return None, f"Sample JRXML generation error: {str(e)}"
    
    def check_library_status(self) -> dict:
        """
        Check the status of the PyJasper library and its dependencies.
        
        Returns:
            Dictionary with status information
        """
        status = {
            'pyjasper_available': True,
            'dependencies': {},
            'features': {}
        }
        
        # Check optional dependencies
        try:
            import matplotlib
            status['dependencies']['matplotlib'] = True
            status['features']['charts'] = True
        except ImportError:
            status['dependencies']['matplotlib'] = False
            status['features']['charts'] = False
        
        try:
            import reportlab
            status['dependencies']['reportlab'] = True
            status['features']['pdf'] = True
        except ImportError:
            status['dependencies']['reportlab'] = False
            status['features']['pdf'] = False
        
        try:
            import PIL
            status['dependencies']['pillow'] = True
            status['features']['images'] = True
        except ImportError:
            status['dependencies']['pillow'] = False
            status['features']['images'] = False
        
        try:
            import openpyxl
            status['dependencies']['openpyxl'] = True
            status['features']['excel'] = True
        except ImportError:
            status['dependencies']['openpyxl'] = False
            status['features']['excel'] = False
        
        # Check database drivers
        try:
            import mysql.connector
            status['dependencies']['mysql'] = True
        except ImportError:
            status['dependencies']['mysql'] = False
        
        try:
            import psycopg2
            status['dependencies']['postgresql'] = True
        except ImportError:
            status['dependencies']['postgresql'] = False
        
        return status


# Global instance for use in the Flask app
pyjasper_integration = PyJasperIntegration()